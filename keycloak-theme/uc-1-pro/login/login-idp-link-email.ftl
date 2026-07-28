<!DOCTYPE html>
<html class="${properties.kcHtmlClass!}">

<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="robots" content="noindex, nofollow">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>${msg("emailLinkIdpTitle", idpDisplayName)}</title>
    <link rel="icon" href="${url.resourcesPath}/img/favicon.ico" />

    <#if properties.stylesCommon?has_content>
        <#list properties.stylesCommon?split(' ') as style>
            <link href="${url.resourcesCommonPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <#if properties.styles?has_content>
        <#list properties.styles?split(' ') as style>
            <link href="${url.resourcesPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
</head>

<body class="uc1-pro-login">
    <div class="login-pf-page">
        <div class="uc1-background"></div>

        <div class="container">
            <div class="row">
                <div class="col-sm-8 col-sm-offset-2 col-md-6 col-md-offset-3 col-lg-6 col-lg-offset-3">
                    <div class="card-pf uc1-card">
                        <header class="login-pf-header">
                            <div class="uc1-logo-container">
                                <img src="${url.resourcesPath}/img/colonel-logo.png" alt="The Colonel Logo" class="uc1-logo" onerror="this.style.display='none'" />
                            </div>
                            <h1 class="uc1-title">Link Account</h1>
                            <p class="uc1-subtitle">Secure sign-in for all services</p>
                        </header>

                        <div id="kc-content">
                            <div id="kc-content-wrapper">
                                <#if message?has_content>
                                    <div class="alert alert-${message.type} uc1-alert" style="margin-bottom: 20px;">
                                        <span class="kc-feedback-text">${kcSanitize(message.summary)?no_esc}</span>
                                    </div>
                                </#if>

                                <p id="instruction1" class="uc1-instruction" style="color: rgba(255,255,255,0.8); margin-bottom: 10px; font-size: 14px; line-height: 1.5;">
                                    ${msg("emailLinkIdp1", idpDisplayName, brokerContext.username, realm.displayName)}
                                </p>
                                <p id="instruction2" class="uc1-instruction" style="color: rgba(255,255,255,0.6); margin-bottom: 20px; font-size: 13px; line-height: 1.5;">
                                    ${msg("emailLinkIdp2")} <a href="${url.loginAction}" class="uc1-link">${msg("doClickHere")}</a> ${msg("emailLinkIdp3")}
                                </p>
                                <p id="instruction3" class="uc1-instruction" style="color: rgba(255,255,255,0.6); font-size: 13px; line-height: 1.5;">
                                    ${msg("emailLinkIdp4")} <a href="${url.loginAction}" class="uc1-link">${msg("doClickHere")}</a> ${msg("emailLinkIdp5")}
                                </p>
                            </div>
                        </div>

                        <footer class="uc1-footer">
                            <p>&copy; 2026 Magic Unicorn Unconventional Technology &amp; Stuff Inc</p>
                        </footer>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
