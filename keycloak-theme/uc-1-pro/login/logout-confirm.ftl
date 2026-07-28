<!DOCTYPE html>
<html class="${properties.kcHtmlClass!}">

<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="robots" content="noindex, nofollow">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Sign Out - Unicorn Commander</title>
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
                            <h1 class="uc1-title">Sign Out</h1>
                            <p class="uc1-subtitle">Unicorn Commander</p>
                        </header>

                        <div id="kc-content">
                            <div id="kc-content-wrapper" style="text-align: center; padding: 20px 0;">

                                <p style="color: rgba(255,255,255,0.8); font-size: 16px; margin-bottom: 25px;">
                                    Are you sure you want to sign out?
                                </p>

                                <div id="kc-form" style="display: flex; gap: 12px; justify-content: center;">
                                    <form method="post" action="${url.logoutConfirmAction}">
                                        <input type="hidden" name="session_code" value="${logoutConfirm.code}"/>
                                        <input class="btn btn-primary btn-lg uc1-submit-btn" style="min-width: 140px;" type="submit" value="Sign Out"/>
                                    </form>

                                    <#if logoutConfirm.skipLink>
                                    <#else>
                                        <#if (client.baseUrl)?has_content>
                                            <a href="${client.baseUrl}" class="btn btn-default btn-lg" style="min-width: 140px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white;">Cancel</a>
                                        </#if>
                                    </#if>
                                </div>

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
