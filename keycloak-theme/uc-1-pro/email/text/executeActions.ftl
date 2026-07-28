Hi<#if user.firstName??> ${user.firstName}</#if>,

To finish setting up your Unicorn Commander account, please complete:
<#if requiredActions??><#list requiredActions as reqActionItem>
  - ${msg("requiredAction." + reqActionItem)}
</#list></#if>

Open this link to continue:
${link}

This link expires in ${linkExpirationFormatter(linkExpiration)}.
If you weren't expecting this, you can ignore this email and nothing will change.

-- Unicorn Commander
