### 启动 Flask application：
flask run --host=0.0.0.0 --port=5001  
### 测试主页：
curl http://127.0.0.1:5001  

### 假设客户端需要同时上传语音和图像文件，可以使用以下 curl 命令测试：

curl -X POST -F "audio=@test.wav" -F "image=@test.jpg" http://127.0.0.1:5001/process

客户端的 example response：
{
  "Input after ASR": " What am I talking about?",
  "LLM output": " What am I talking about? test.jpg",
  "TTS URL": "http://192.168.0.20:5001/output/output.mp3"
}


后端 example response
== index called ==
127.0.0.1 - - [02/Jan/2025 17:34:44] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [02/Jan/2025 17:35:03] "POST /process HTTP/1.1" 200 -
127.0.0.1 - - [02/Jan/2025 17:35:03] "GET /audio/photo.mp3 HTTP/1.1" 200 -
127.0.0.1 - - [02/Jan/2025 17:35:10] "POST /process HTTP/1.1" 200 -
127.0.0.1 - - [02/Jan/2025 17:35:10] "GET /audio/photo.mp3 HTTP/1.1" 200 -
127.0.0.1 - - [02/Jan/2025 17:35:25] "POST /process HTTP/1.1" 200 -
127.0.0.1 - - [02/Jan/2025 17:35:25] "GET /audio/photo.mp3 HTTP/1.1" 200 -
127.0.0.1 - - [02/Jan/2025 17:37:07] "POST /process HTTP/1.1" 200 -
127.0.0.1 - - [02/Jan/2025 17:37:07] "GET /audio/photo.mp3 HTTP/1.1" 200 -
127.0.0.1 - - [03/Jan/2025 14:22:22] "POST /process HTTP/1.1" 400 -

目前的逻辑：如果请求中缺少语音或图像，后端会直接返回错误，而不会尝试部分处理


整个通信流程：
客户端把语音和图片输入 POST 到 http://192.168.0.20:5001/process ->
后端把 inputs 放入 ./uploads 文件夹 ->
后端用 LLM 推理 inputs，再用 TTS 生成最终语音，将其放入 ./outputs 文件夹 ->
后端把返回语音放在 http://192.168.0.20:5001/output ->
客户端从这个 URL GET 最终语音



安卓客户端 fetch output file using HTTP library OkHttp：
```kotlin
val client = OkHttpClient()

val request = Request.Builder()
    .url("http://192.168.0.20:5001/output/output.mp3") # 目前这个是静态的文件，也可以调用response url - 更 dynamical and flexible
    .get()
    .build()

client.newCall(request).enqueue(object : Callback {
    override fun onFailure(call: Call, e: IOException) {
        Log.e("TTSDownload", "Failed to download audio: $e")
    }

    override fun onResponse(call: Call, response: Response) {
        if (response.isSuccessful) {
            val inputStream = response.body?.byteStream()
            val file = File(context.filesDir, "output.mp3")
            file.outputStream().use { outputStream ->
                inputStream?.copyTo(outputStream)
            }
            Log.d("TTSDownload", "Audio file downloaded successfully: ${file.path}")
        } else {
            Log.e("TTSDownload", "Failed to download audio. Code: ${response.code}")
        }
    }
})
```




