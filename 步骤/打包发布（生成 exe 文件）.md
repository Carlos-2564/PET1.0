做好的桌宠可以打包成 exe 文件，发给没有 Python 环境的朋友也能直接用，步骤超简单：

1. 安装打包工具
在命令提示符中输入：

pip install pyinstaller
2. 准备图标（可选）
找一张喜欢的图标图片（.ico 格式），放到项目文件夹里，命名为icon.ico（没有也可以跳过，用默认图标）。制作ico文件的在线网址：PNG转ICO批量转换器 | 线上 免费

3. 执行打包命令
在pycharm终端中输入：

pyinstaller --onefile --name 恋与深空桌宠（可替换成你自己想要的名称） --noconsole --icon=favicon.ico --add-data "gif/*;gif" --add-data "config.json;." zhuochong.py    
-F：生成单个 exe 文件（方便分享）；
-w：去掉黑框控制台（更美观）；
-i icon.ico：设置图标（没有图标可省略）；
--name 恋与深空桌宠（可替换成你自己想要的名称）；

--icon=favicon.ico（favicon为你的ico文件名称）；

zhuochong.py（为你的桌宠代码名称）；
4. 整理文件
打包完成后，在项目文件夹的dist目录里找到桌宠.exe，双击即可运行。

5. 运行桌宠
双击桌宠.exe，你的专属桌宠就启动啦！右键点击可调出菜单       