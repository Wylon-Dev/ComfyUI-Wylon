// Run Python without relying on a POSIX-only python3 command or a shell.
import { spawnSync } from 'node:child_process';

const command = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const result = spawnSync(command, process.argv.slice(2), { stdio: 'inherit' });
if (result.error) console.error(`Could not run Python (${command}): ${result.error.message}`);
process.exitCode = result.status ?? 1;
