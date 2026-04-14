import { isFunction } from './typeof2'
import type { MutableRefObject } from 'react'

type TargetValue<T> = T | undefined | null

type TargetType = HTMLElement | Element | Window | Document

export type BasicTarget<T extends TargetType = Element> = | (() => TargetValue<T>) | TargetValue<T> | MutableRefObject<TargetValue<T>>

export default function getTargetElement<T extends TargetType> (target: BasicTarget<T>, defaultElement?: T) {
  if (!target) {
    return defaultElement
  }

  let targetElement: TargetValue<T>

  if (isFunction(target)) {
    targetElement = target()
  } else if ('current' in target) {
    targetElement = target.current
  } else {
    targetElement = target
  }

  return targetElement
}
