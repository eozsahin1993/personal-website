---
layout: post
title: "TIL: React Class vs Function Components"
categories:
  - Posts
tags:
  - Today I learned
  - React
  - Web
---

Today, I was updating one of the existing React components in our Kustomer web codebase to prefetch saved search graph data upon a property change. Our existing React component appeared to be a class component like below:

```tsx
export class SearchLayout extends React.Component<React.PropsWithChildren<SearchLayoutProps>> {
    componentDidMount() {
        // Component logic...
    }

    componentDidUpdate() {
        // Component logic..
    }

    render() {
        <div>
            { /* Render component */ }
        </div>
    }

}
```

Up until this point, I knew that you could create React components either by extending React.Component class or simply creating a function like below: 

```tsx
export default function SearchLayout(props: SearchLayoutProps) {
    // Component logic..
    return (
        <div>
            { /* Render component */ }
        </div>
    );
} 
```

As someone still relatively new to web development, I immediately realized something was wrong when I tried adding the `useEffect()` hook to our class component. It turns out, this is not even supported with React class components and that's what I learned today. I decided to do more research about the history and differences between two styles and share my findings..

### React Class Components

An example Class Component in [react.dev](https://react.dev/reference/react/Component#defining-a-class-component):
```jsx
import { Component } from 'react';

class Greeting extends Component {
  render() {
    return <h1>Hello, {this.props.name}!</h1>;
  }
}
```

According to the docs:

1. A `return() {}` has to be specified.
2. The props can be accessed via `this.props`.
3. `React hooks` are not supported!
4. Component state managed by internal `this.state` and `this.setState()`.
5. Has lifecycle methods such as: 
    - `componentDidMount()`: Component is added to the screen
    - `componentDidUpdate()`: Component rerenders due to props or state changes
    - `componentWillUnmount()`: Component is removed from the screen
    - `componentDidCatch()`: Component threw an error 


### React Function Component

An example function component in [react.dev](https://react.dev/reference/react/Component#alternatives)
```jsx
function Greeting({ name }) {
  return <h1>Hello, {name}!</h1>;
}
```

According to the docs:
1. Supports React Hooks like `useState()` and `useEffect()` 
2. Properties (`props`) can be directly accessed via function parameters.
3. State is managed via hooks such as `useState()` instead of `this.state`.
4. Does not rely on traditional lifecycle methods. Instead, hooks like useEffect() handle side effects.


### Verdict

According to the official documentation, it is **recommended** to convert all class components into function components.

Before React hooks were introduced, if your component had a state or if you wanted utilize the lifecycle methods, you **had** to use a class component. Over time, different React hooks were added such as

- `useState()` which allowed you retain state in a function component.
- `useEffect()` which changes the whole lifecycle methodology for the good. These changes were also similar to how Jetpack Compose (declarative UI library for Android) introduced new state changes. Essentially, `useEffect()` accepts a parameter and the lambda function is triggered when that state changes.
- `useContext()` allows you to read and subscribe to context within your application.
- Creating custom hooks by both using `useState()` and `useEffect()`

React Hooks offer significantly more functionality and flexibility compared to class component lifecycle methods. They make components more extensible and adaptable to future updates, whereas class components are now considered legacy.Thus, we should strive to use function components going forward.

Stay tuned for more articles, happy coding!

#### Resources 
- [https://react.dev/reference/react](https://react.dev/reference/react)
- [https://ui.dev/why-react-hooks](https://ui.dev/why-react-hooks)
