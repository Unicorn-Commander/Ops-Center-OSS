<html>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2a2a35;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="520" cellpadding="0" cellspacing="0" style="max-width:520px;width:100%;background:#ffffff;border:1px solid #ececf0;border-radius:12px;">
        <tr><td style="padding:28px 32px 8px;font-size:18px;font-weight:600;color:#5b21b6;">Unicorn Commander</td></tr>
        <tr><td style="padding:8px 32px 0;font-size:15px;line-height:1.6;">
          <p style="margin:0 0 14px;">Hi<#if user.firstName??> ${user.firstName}</#if>,</p>
          <p style="margin:0 0 14px;">Please confirm this is your email address for your Unicorn Commander account.</p>
        </td></tr>
        <tr><td align="center" style="padding:24px 32px;">
          <a href="${link}" style="background:#6d28d9;color:#ffffff;text-decoration:none;padding:13px 30px;border-radius:8px;font-size:15px;font-weight:600;display:inline-block;">Confirm email</a>
        </td></tr>
        <tr><td style="padding:0 32px;font-size:13px;line-height:1.6;color:#6b6b76;">
          <p style="margin:0 0 10px;">Or paste this link into your browser:<br><span style="color:#5b21b6;word-break:break-all;">${link}</span></p>
          <p style="margin:0 0 10px;">This link expires in ${linkExpirationFormatter(linkExpiration)}.</p>
          <p style="margin:0 0 10px;">If you didn't create this account, you can safely ignore this email.</p>
        </td></tr>
        <tr><td style="padding:18px 32px 26px;border-top:1px solid #ececf0;font-size:12px;color:#9a9aa5;">
          Unicorn Commander &middot; automated account message
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
