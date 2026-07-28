<!DOCTYPE html>
<html class="${properties.kcHtmlClass!}">

<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="robots" content="noindex, nofollow">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <#if properties.meta?has_content>
        <#list properties.meta?split(' ') as meta>
            <meta name="${meta?split('==')[0]}" content="${meta?split('==')[1]}"/>
        </#list>
    </#if>

    <title>${msg("loginTitle",(realm.displayName!''))}</title>
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
                            <h1 class="uc1-title">${msg("loginTitle",(realm.displayName!''))}</h1>
                            <p class="uc1-subtitle">Secure sign-in for all services</p>
                        </header>

                        <div id="kc-content">
                            <div id="kc-content-wrapper">
                                <#if message?has_content>
                                    <div class="alert alert-${message.type} uc1-alert" style="margin-bottom: 20px;">
                                        <span class="kc-feedback-text">${kcSanitize(message.summary)?no_esc}</span>
                                    </div>
                                </#if>

                                <#if requiredActions??>
                                    <p class="uc1-instruction" style="color: rgba(255,255,255,0.8); margin-bottom: 20px; font-size: 14px; line-height: 1.5;">
                                        <#list requiredActions>
                                            <#items as reqActionItem>${kcSanitize(msg("requiredAction.${reqActionItem}"))?no_esc}<#sep>, </#sep></#items>
                                        </#list>
                                    </p>
                                </#if>

                                <#if skipLink??>
                                <#else>
                                    <#if pageRedirectUri?has_content>
                                        <div id="kc-info-message" class="uc1-button-group" style="margin-top: 20px;">
                                            <a href="${pageRedirectUri}" class="btn btn-primary btn-block btn-lg uc1-submit-btn" style="display: block; text-align: center; text-decoration: none;">${kcSanitize(msg("backToApplication"))?no_esc}</a>
                                        </div>
                                    <#elseif actionUri?has_content>
                                        <div id="kc-info-message" class="uc1-button-group" style="margin-top: 20px;">
                                            <a href="${actionUri}" class="btn btn-primary btn-block btn-lg uc1-submit-btn" style="display: block; text-align: center; text-decoration: none;">${kcSanitize(msg("proceedWithAction"))?no_esc}</a>
                                        </div>
                                    <#elseif (client.baseUrl)?has_content>
                                        <div id="kc-info-message" class="uc1-button-group" style="margin-top: 20px;">
                                            <a href="${client.baseUrl}" class="btn btn-primary btn-block btn-lg uc1-submit-btn" style="display: block; text-align: center; text-decoration: none;">${kcSanitize(msg("backToApplication"))?no_esc}</a>
                                        </div>
                                    </#if>
                                </#if>
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
