const { spawn } = require("child_process");
const path = require("path");

const projectRoot = path.resolve(__dirname, "..");

const python = path.join(
  projectRoot,
  ".venv",
  "Scripts",
  "python.exe"
);

const server = path.join(
  projectRoot,
  "server",
  "mcp_server.py"
);

const child = spawn(python, [server], {
  cwd: projectRoot,
  stdio: "inherit"
});

child.on("error", (error) => {
  console.error("Failed to start MCP server:", error);
});

child.on("exit", (code) => {
  process.exit(code ?? 0);
});