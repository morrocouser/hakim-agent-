import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import assert from 'node:assert/strict'

const root = resolve(import.meta.dirname, '..')
const read = (path) => readFile(resolve(root, path), 'utf8')

const css = await read('app/globals.css')
assert.match(css, /--surface-raised:/, 'The control-room raised surface token is required')
assert.match(css, /--focus-ring:/, 'The keyboard focus token is required')
assert.match(css, /prefers-reduced-motion/, 'Reduced-motion support is required')

const shell = await read('components/AppShell.tsx')
assert.match(shell, /aria-expanded/, 'The mobile navigation toggle needs aria-expanded')
assert.match(shell, /Escape/, 'The mobile navigation must close with Escape')

const kit = await read('components/ui-kit.tsx')
assert.match(kit, /export function Panel/, 'Panel must be a shared primitive')
assert.match(kit, /export function StatusBadge/, 'StatusBadge must be a shared primitive')

console.log('Control-room UI contract: OK')
