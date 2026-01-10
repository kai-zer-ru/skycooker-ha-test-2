import { nodeResolve } from '@rollup/plugin-node-resolve';
import typescript from '@rollup/plugin-typescript';

export default {
  input: 'src/skycooker-card.ts',
  output: {
    dir: 'dist',
    format: 'es',
  },
  plugins: [nodeResolve(), typescript()],
};