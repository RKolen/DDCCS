declare module 'dotenv' {
  interface DotenvConfigOptions {
    path?: string;
  }
  function config(options?: DotenvConfigOptions): void;
  export default { config };
}
