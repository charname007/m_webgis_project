
import re

class SQLValidator:
    """
    一个简单的SQL验证器，确保只执行安全的SELECT查询。
    """

    def __init__(self):
        # 定义不允许的关键词（不区分大小写）
        self.forbidden_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE',
            'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'MERGE', 'EXEC', 'EXECUTE'
        ]
        # 构建一个正则表达式，用于一次性匹配所有禁用词
        # \b 确保匹配整个单词
        self.forbidden_pattern = re.compile(r'\b(' + '|'.join(self.forbidden_keywords) + r')\b', re.IGNORECASE)

    def validate(self, sql: str) -> (bool, str):
        """
        验证SQL查询的安全性。

        Args:
            sql: 要验证的SQL查询字符串。

        Returns:
            一个元组 (is_safe, message)，其中 is_safe 是布尔值，message 是描述。
        """
        # 检查是否为 SELECT 语句
        if not sql.strip().upper().startswith('SELECT'):
            return False, "Security Error: Only SELECT queries are allowed."

        # 检查是否包含禁用关键词
        match = self.forbidden_pattern.search(sql)
        if match:
            forbidden_word = match.group(0)
            return False, f"Security Error: Query contains forbidden keyword '{forbidden_word}'."
        
        # 如果所有检查都通过
        return True, "Query is safe."
