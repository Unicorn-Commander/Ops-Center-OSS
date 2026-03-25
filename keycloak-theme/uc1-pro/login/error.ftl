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

    <title>${msg("errorTitle",(realm.displayName!''))}</title>
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
    <#if properties.scripts?has_content>
        <#list properties.scripts?split(' ') as script>
            <script src="${url.resourcesPath}/${script}" type="text/javascript"></script>
        </#list>
    </#if>
    <#if scripts??>
        <#list scripts as script>
            <script src="${script}" type="text/javascript"></script>
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
                                <img src="${url.resourcesPath}/img/company-logo.png" alt="Your Company" class="uc1-logo" onerror="this.style.display='none'" />
                            </div>
                            <h1 class="uc1-title">Your Company</h1>
                            <p class="uc1-subtitle">Applied Research &bull; Advanced Development &bull; Rapid Iteration</p>
                        </header>

                        <div id="kc-content">
                            <div id="kc-content-wrapper">
                                <div class="alert alert-error uc1-alert">
                                    <span class="pficon pficon-error-circle-o"></span>
                                    <span class="kc-feedback-text"><#if message?? && message.summary??>${kcSanitize(message.summary)?no_esc}<#else>An unexpected error occurred.</#if></span>
                                </div>

                                <div id="kc-error-actions" style="text-align: center; margin-top: 25px;">
                                    <#if skipLink?? && skipLink>
                                    <#else>
                                        <#if client?? && client.baseUrl?has_content>
                                            <a href="${client.baseUrl}" class="uc1-submit-btn" style="display: inline-block; text-decoration: none; margin-bottom: 12px;">Back to Application</a>
                                        </#if>
                                    </#if>
                                    <#if url.loginUrl??>
                                        <p style="margin-top: 15px;">
                                            <a href="${url.loginUrl}" class="uc1-link">Try signing in again</a>
                                        </p>
                                    </#if>
                                </div>
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
