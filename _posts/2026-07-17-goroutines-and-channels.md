---
layout: post
title: "Goroutines and channels"
categories:
  - Posts
tags:
  - Golang
  - Go
  - concurrency
---

While building [RagPack](www.ragpack.dev), I needed a file worker that would parse file chunks and write them into LanceDB, an embedded columnar vector database. This would have been fiddly to get right in most languages, but Go's concurrency primitives made it simple without any major architectural shift. Here's how goroutines, channels, and `sync.WaitGroup` work together in the ingestion pipeline.

### What are goroutines?

Goroutines, just like coroutines in Kotlin, are lightweight concurrency units managed by the Go runtime. The runtime multiplexes many goroutines onto a much smaller number of OS threads, so spawning thousands of them is cheap.

Launching one is one line:

```go
go func() {}()
```

In my case, I spawn a fixed number of worker goroutines based on the configured worker count:

```go
for i := 0; i < workers; i++ {
  wp.waitGroup.Add(1)
  go wp.run(ctx)
}
```

Since each goroutine runs independently, something has to coordinate handing off work between them and knowing when they're actually done. That's where channels and `WaitGroup` come in, and they solve two completely different problems.

### Channels move the work

A channel is the communication layer between concurrent goroutines, where each can send and receive values safely, without explicit locks or race conditions.

In my case, workers pull queued items off a shared channel:

```go
type queueItem struct {
	job    meta.Job
	reader io.ReadCloser
}

queue := make(chan queueItem, workers*10)
```

Data flows through the `<-` operator:

- Send to a channel: `ch <- item`
- Receive from a channel: `item := <-ch`

There are two flavors, and they behave differently based on capacity:

**Unbuffered channels** have no capacity to hold data. A send blocks the sender until a receiver is ready, and a receiver blocks until a sender sends. This synchronizes the two goroutines directly.

**Buffered channels** are created with a fixed capacity, like `make(chan queueItem, 10)`. Sending only blocks once the buffer is full, receiving only blocks once it's empty. That decouples the timing of sender and receiver, which is why my queue channel above is buffered at `workers*10`, it lets jobs pile up a bit without forcing whoever's submitting them to wait on a free worker.

Sending on an unbuffered channel with nobody reading deadlocks the whole program:

```go
func main() {
	ch := make(chan queueItem)
	ch <- queueItem{} // ERROR: deadlock, nothing is ever reading from ch
}
```

Each worker in my pool avoids this by always being ready to receive, looping on a `select` that watches both the queue and cancellation:

```go
func (wp *WorkerPool) run(ctx context.Context) {
	defer wp.waitGroup.Done()
	for {
		select {
		case <-ctx.Done():
			return
		case item := <-wp.queue:
			if err := wp.processJob(ctx, item); err != nil {
				log.Printf("ingester: job %s failed: %v", item.job.ID, err)
			}
		}
	}
}
```

This is what makes the producer/consumer pattern so easy in Go. There's no thread pool to manage and no lock to take, just a channel read in a loop.

### WaitGroup answers a different question

I initially assumed WaitGroup was somehow gating the channel, blocking new work until a slot opened up. It isn't, and it has no idea what a channel even is. It's a plain counter with three methods:

- `Add(n)`: increments the counter by `n`, called before spawning the goroutines you want tracked
- `Done()`: decrements the counter by one, called by each goroutine when it finishes, usually via `defer`
- `Wait()`: blocks the calling goroutine until the counter hits zero

What it actually answers is: "have all the goroutines I started actually finished?" Canceling `ctx` tells workers to stop picking up *new* jobs, but it says nothing about a job already in progress. A worker could be mid-write to LanceDB the instant `ctx` is canceled, and if the process exits right then, that write is lost.

```go
func (wp *WorkerPool) Stop() {
	wp.waitGroup.Wait()
}
```

`Stop()` is called after the context is canceled, and it blocks until every worker's deferred `wp.waitGroup.Done()` has actually run, meaning every in-flight job finished processing first. Skip this and shutdown becomes a race: clean most of the time, but occasionally losing the tail end of whatever a worker was writing.

### Putting it together

`run` and `Stop` above are two of the three moving pieces. The dispatcher ties them together:

```go
func (wp *WorkerPool) Start(ctx context.Context, workers int) {
	go wp.loop(ctx, workers)
}

func (wp *WorkerPool) loop(ctx context.Context, workers int) {
	for i := 0; i < workers; i++ {
		wp.waitGroup.Add(1)
		go wp.run(ctx)
	}

	for {
		select {
		case <-ctx.Done():
			return
		}
	}
}
```

`Start` kicks off the dispatcher in its own goroutine. The dispatcher spawns the fixed pool of workers, each incrementing the shared WaitGroup before it starts. Every worker pulls from the same queue channel until the context is canceled. `Stop` is the only place that actually confirms shutdown is done, not when the context is canceled, but when the last worker's Done call lands.

Three primitives, three separate jobs: goroutines run the work, the channel distributes it, `WaitGroup` confirms it's finished.

Happy coding!
