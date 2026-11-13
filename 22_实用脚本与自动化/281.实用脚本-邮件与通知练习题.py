# ===== 第281课：实用脚本-邮件与通知 =====
# 知识点：
#   - email.message.EmailMessage：构造邮件（主题/正文/附件）
#   - smtplib.SMTP_SSL + 授权码发送；授权码≠登录密码
#   - 密钥走环境变量（第217课），绝不硬编码
#   - 本课只“构造并保存为 .eml”，真实发送步骤看注释

from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

# ---- 构造邮件 ----
msg = EmailMessage()
msg["From"] = formataddr(("监控机器人", "bot@example.com"))
msg["To"] = "admin@example.com"
msg["Subject"] = "【告警】磁盘空间不足"

body = "C 盘使用率 92%，请及时清理。\n触发时间：2026-11-12 23:00"
msg.set_content(body)                                  # 纯文本正文

# 添加附件（bytes + 类型 + 文件名）
msg.add_attachment(
    b"metric,value\ndisk,92",
    maintype="text", subtype="csv", filename="stats.csv",
)

# 保存为 .eml（邮件客户端可直接打开查看效果）
Path("alert.eml").write_bytes(bytes(msg))

print("主题：", msg["Subject"])
print("正文：", body.splitlines()[0])
print("附件：", [p.get_filename() for p in msg.iter_attachments()])
print("已生成 alert.eml（可用 Foxmail/Outlook/网页邮箱打开验证）")

# ---- 真实发送（以 QQ 邮箱为例，需先在网页邮箱开启 SMTP 获得授权码）----
# import os, smtplib
# with smtplib.SMTP_SSL("smtp.qq.com", 465) as smtp:
#     smtp.login(os.environ["MAIL_USER"], os.environ["MAIL_AUTH_CODE"])
#     smtp.send_message(msg)
# 常见端口：465(SSL) / 587(STARTTLS)；163 邮箱是 smtp.163.com

Path("alert.eml").unlink()      # 清理演示文件

# ===== 练习题 =====
# 1. 给邮件加“多收件人”：msg["To"] 逗号分隔，或用 add_cc 抄送。
# 2. 把一个真实小文件（如日志）作为附件发送。
# 3. 编写 send_alert(subject, body) 函数：配置齐全才发送，否则打印降级提示。
# 4. 思考：为什么邮箱服务商要区分“授权码”和“登录密码”？
