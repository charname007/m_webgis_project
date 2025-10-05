"""检查数据库中的数据"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import DatabaseConnector

db = DatabaseConnector()

# 检查浙江省5A景区
print("=== 检查浙江省5A景区 ===")
result = db.execute_raw_query("""
    SELECT "所属省份", level, COUNT(*) as count
    FROM a_sight
    WHERE "所属省份" LIKE '%浙江%'
    GROUP BY "所属省份", level
    ORDER BY count DESC
""")

for row in result:
    print(f"{row['所属省份']} - {row['level']}: {row['count']}条")

print("\n=== 前5条浙江省景区 ===")
result2 = db.execute_raw_query("""
    SELECT name, level, "所属省份", "所属城市"
    FROM a_sight
    WHERE "所属省份" LIKE '%浙江%'
    LIMIT 5
""")

for row in result2:
    print(f"{row['name']} ({row['level']}) - {row['所属省份']} {row['所属城市']}")

db.close()
