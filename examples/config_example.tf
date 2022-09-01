version = 1

http = {
  port = 10001
  transport = {
    timeout = 60.0
    buffer_size = 65535
  }
  interfaces = [
      "127.0.0.1", "192.168.0.1"
  ]
}
