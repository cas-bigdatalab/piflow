import type {} from 'react'

declare module 'react/jsx-runtime' {
  namespace JSX {
    interface IntrinsicElements {
      'iconify-icon': React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & {
          icon?: string
          width?: string | number
          height?: string | number
        },
        HTMLElement
      >
    }
  }
}
