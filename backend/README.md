cd backend
安装
pip install -r requirements.txt
启动
uvicorn app.main:app --reload

导入数据 python data_importer.py --file "xxx" 会自动创建es的customs_data索引

启动后自动创建es的customs_users索引