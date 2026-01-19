# coding=utf-8
"""
消息发送器模块（统一朗文品牌版）

支持：
- Email
- Feishu / DingTalk / WeCom / Telegram / Slack / ntfy / Bark
"""

import smtplib
import time
import json
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

import requests

from .batch import add_batch_headers, get_max_batch_header_size
from .formatters import convert_markdown_to_mrkdwn, strip_markdown


# ============================================================================
# SMTP CONFIG
# ============================================================================
SMTP_CONFIGS = {
    "gmail.com": {"server": "smtp.gmail.com", "port": 587, "encryption": "TLS"},
    "qq.com": {"server": "smtp.qq.com", "port": 465, "encryption": "SSL"},
    "outlook.com": {"server": "smtp-mail.outlook.com", "port": 587, "encryption": "TLS"},
    "hotmail.com": {"server": "smtp-mail.outlook.com", "port": 587, "encryption": "TLS"},
    "live.com": {"server": "smtp-mail.outlook.com", "port": 587, "encryption": "TLS"},
    "163.com": {"server": "smtp.163.com", "port": 465, "encryption": "SSL"},
    "126.com": {"server": "smtp.126.com", "port": 465, "encryption": "SSL"},
    "sina.com": {"server": "smtp.sina.com", "port": 465, "encryption": "SSL"},
    "sohu.com": {"server": "smtp.sohu.com", "port": 465, "encryption": "SSL"},
    "189.cn": {"server": "smtp.189.cn", "port": 465, "encryption": "SSL"},
    "aliyun.com": {"server": "smtp.aliyun.com", "port": 465, "encryption": "TLS"},
}


# ============================================================================
# EMAIL SENDER（朗文品牌版）
# ============================================================================
def send_to_email(
    from_email: str,
    password: str,
    to_email: str,
    report_type: str,
    html_file_path: str,
    custom_smtp_server: Optional[str] = None,
    custom_smtp_port: Optional[int] = None,
    *,
    get_time_func: Callable = None,
    ai_analysis: Any = None,
    ai_push_mode: str = "both",
) -> bool:
    """
    发送邮件通知（朗文｜全球农业照明要闻 · 每日推送）
    """
    try:
        if not html_file_path or not Path(html_file_path).exists():
            print(f"❌ HTML 文件不存在: {html_file_path}")
            return False

        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # === SMTP 判断 ===
        domain = from_email.split("@")[-1].lower()

        if custom_smtp_server and custom_smtp_port:
            smtp_server = custom_smtp_server
            smtp_port = int(custom_smtp_port)
            use_tls = smtp_port == 587
        elif domain in SMTP_CONFIGS:
            cfg = SMTP_CONFIGS[domain]
            smtp_server = cfg["server"]
            smtp_port = cfg["port"]
            use_tls = cfg["encryption"] == "TLS"
        else:
            smtp_server = f"smtp.{domain}"
            smtp_port = 587
            use_tls = True

        msg = MIMEMultipart("alternative")

        # === 发件人（品牌固定）===
        sender_name = "Number 朗文市场部每日推荐程序"
        msg["From"] = formataddr((sender_name, from_email))

        # === 收件人 ===
        recipients = [x.strip() for x in to_email.split(",") if x.strip()]
        if not recipients:
            print("❌ EMAIL_TO 为空")
            return False
        msg["To"] = ", ".join(recipients)

        # === 邮件标题（核心修正点）===
        now = get_time_func() if get_time_func else datetime.now()
        subject = f"朗文｜全球农业照明要闻 · 每日推送（{now.strftime('%m-%d')}）"
        msg["Subject"] = Header(subject, "utf-8")

        print("✅ EMAIL SUBJECT ACTIVE:", subject)

        # === 标准 Header ===
        msg["MIME-Version"] = "1.0"
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        # === 纯文本兜底 ===
        text_part = MIMEText(
            f"""朗文｜全球农业照明要闻 · 每日推送
生成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}

请使用支持 HTML 的邮件客户端查看完整内容。
""",
            "plain",
            "utf-8",
        )
        msg.attach(text_part)

        # === HTML 正文 ===
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # === 发送 ===
        if use_tls:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)

        server.login(from_email, password)
        server.send_message(msg)
        server.quit()

        print(f"✅ 邮件发送成功 [朗文每日推送] -> {msg['To']}")
        return True

    except Exception as e:
        print("❌ 邮件发送失败：", e)
        return False
