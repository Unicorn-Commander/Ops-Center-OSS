Hi<#if user.firstName??> ${user.firstName}</#if>,

We received a request to reset the password for your Unicorn Commander account.
Open this link to choose a new password:
${link}

This link expires in ${linkExpirationFormatter(linkExpiration)}.
If you didn't request a password reset, you can ignore this email -- your password won't change.

-- Unicorn Commander
