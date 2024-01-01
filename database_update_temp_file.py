import global_var
import settings
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import SQLConnector

sql = SQLConnector(settings.database_user, settings.database_password, 'entertainment')

data = JSONEditor(global_var.show_download_database).read()

for show in data.keys():
    for episode in data[show]:
        columns = "name, episode_id, episode_name, magnet, quality"
        if episode['episode_id'] != "Test" and episode['episode_id'] != "test":
            val = (show, episode['episode_id'], episode['episode_name'], episode['magnet'], episode['quality'])
            sql.insert('tv_show', columns, val)
