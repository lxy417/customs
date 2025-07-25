const https = require('https');
const fs = require('fs');
const path = require('path');

const imageUrl = 'https://comtradeplus.un.org/images/AdobeStock_290092195.jpeg';
const imagePath = path.join(__dirname, 'public', 'images');
const imageName = 'background.jpeg';

// 创建images目录（如果不存在）
if (!fs.existsSync(imagePath)) {
  fs.mkdirSync(imagePath, { recursive: true });
}

const file = fs.createWriteStream(path.join(imagePath, imageName));

console.log('开始下载背景图片...');

https.get(imageUrl, (response) => {
  if (response.statusCode === 200) {
    response.pipe(file);
    
    file.on('finish', () => {
      file.close();
      console.log(`✅ 背景图片下载完成: ${path.join(imagePath, imageName)}`);
    });
  } else {
    console.error(`❌ 下载失败，状态码: ${response.statusCode}`);
  }
}).on('error', (err) => {
  fs.unlink(path.join(imagePath, imageName), () => {});
  console.error(`❌ 下载错误: ${err.message}`);
});