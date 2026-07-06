module.exports = {
  apps: [{
    name: 'zkoner-tunnel',
    script: 'npx',
    args: 'localtunnel --port 8000',
    cwd: '/home/zxm/zkoner/backend',
    max_restarts: 10,
    restart_delay: 5000,
    log_file: '/home/zxm/zkoner/data/tunnel-pm2.log',
    env: {
      PATH: process.env.PATH,
      HOME: process.env.HOME,
    }
  }]
};
