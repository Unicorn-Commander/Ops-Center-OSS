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
    <link href="${url.resourcesPath}/css/login.css" rel="stylesheet" />
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
                                <img src="${url.resourcesPath}/img/company-logo.png" alt="Your Company" class="uc1-logo" onerror="this.style.display='none'" />
                            </div>
                            <h1 class="uc1-title">Your Company</h1>
                            <p class="uc1-subtitle">Applied Research &bull; Advanced Development &bull; Rapid Iteration</p>
                        </header>

                        <div id="kc-content">
                            <div id="kc-content-wrapper">
                                <p style="color: var(--uc1-text-secondary); font-size: 15px; text-align: center; margin-bottom: 24px;">
                                    ${msg("logoutConfirmHeader")}
                                </p>

                                <form action="${url.logoutConfirmAction}" method="POST" class="uc1-form">
                                    <input type="hidden" name="session_code" value="${logoutConfirm.code}">
                                    <div class="form-group uc1-button-group">
                                        <input tabindex="4" class="btn btn-primary btn-block btn-lg uc1-submit-btn"
                                               name="confirmLogout" id="kc-logout" type="submit" value="${msg("doLogout")}"/>
                                    </div>
                                </form>

                                <#if !logoutConfirm.skipLink>
                                    <#if (client?? && client.baseUrl?has_content)>
                                        <div class="uc1-registration" style="margin-top: 15px;">
                                            <span><a href="${client.baseUrl}" class="uc1-link">${kcSanitize(msg("backToApplication"))?no_esc}</a></span>
                                        </div>
                                    </#if>
                                </#if>
                            </div>
                        </div>

                        <footer class="uc1-footer">
                            <p>&copy; 2026 Magic Unicorn Unconventional Technology & Stuff Inc</p>
                        </footer>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
