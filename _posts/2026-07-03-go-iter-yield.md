---
layout: post
title: "TIL: Streaming Data in Go with iter and yield"
categories:
  - Posts
tags:
  - Today I learned
  - Go
---

While building [RagPack](https://github.com/eozsahin1993/ragpack), a library that chunks files for embedding, I needed a common way to stream parsed content from multiple file formats. RagPack supports CSV, PDF, DOCX, HTML, XLSX, Markdown, JSON and more. Each format has its own parser, but the ingester that consumes them should not care which one it is talking to. I needed a shared contract. In Java I would have reached for an `Iterator<T>` or an `InputStream`, but in Go the answer turned out to be the `iter` package, introduced in Go 1.23.

### The Parser interface

The `iter` package introduces two types. `Seq[V]` yields a single value at a time, and `Seq2[K, V]` yields a pair:

```go
type Seq[V any]     func(yield func(V) bool)
type Seq2[K, V any] func(yield func(K, V) bool)
```

`Seq2` is the right fit here because each iteration naturally produces two things: a parsed unit and any read error. This matches Go's standard `(value, error)` convention and lets the caller handle errors inline without wrapping them in a struct.

That made `iter.Seq2[Unit, error]` a natural return type for the `Parser` interface:

```go
type Parser interface {
    Parse(ctx context.Context, r io.ReadCloser) iter.Seq2[Unit, error]
}
```

Every sub-parser, `CSVParser`, `PDFParser`, `DocxParser`, `HTMLParser` and so on, implements this one method. The ingester does not need to know which format it is dealing with.

### Implementing a parser

Here is what a parser implementation looks like:

```go
func (p *Parser) Parse(_ context.Context, r io.ReadCloser) iter.Seq2[Unit, error] {
    return func(yield func(Unit, error) bool) {
        defer r.Close()

        reader := bufio.NewReader(r)
        for {
            line, err := reader.ReadString('\n')
            if err == io.EOF {
                break
            }
            if err != nil {
                yield(Unit{}, err)
                return
            }
            if !yield(Unit{Text: strings.TrimRight(line, "\n")}, nil) {
                return
            }
        }
    }
}
```

The `if !yield(...) { return }` part is the key. If the caller breaks out of the loop early, `yield` returns `false` and we stop reading. No wasted work.

### Using it with range

Because all parsers return the same type, the ingester ranges over any of them the same way:

```go
for unit, err := range parser.Parse(ctx, file) {
    if err != nil {
        // handle error
    }
    embed(unit)
}
```

Swap in a different parser and the loop does not change. That is one big win. Memory was also in our minds when designing this. For streaming formats like CSV, JSON, or plain text, yielding one unit at a time keeps the footprint flat no matter how large the file is. For formats like PDF it is a bit more nuanced since the underlying parser has to load the full file first to parse it.

Happy coding!
