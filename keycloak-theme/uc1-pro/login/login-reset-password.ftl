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

    <title>${msg("emailForgotTitle",(realm.displayName!''))}</title>
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
                                <#if message?has_content && (message.type != 'warning' || !isAppInitiatedAction??)>
                                    <div class="alert alert-${message.type} uc1-alert">
                                        <#if message.type = 'success'><span class="pficon pficon-ok"></span></#if>
                                        <#if message.type = 'warning'><span class="pficon pficon-warning-triangle-o"></span></#if>
                                        <#if message.type = 'error'><span class="pficon pficon-error-circle-o"></span></#if>
                                        <#if message.type = 'info'><span class="pficon pficon-info"></span></#if>
                                        <span class="kc-feedback-text">${kcSanitize(message.summary)?no_esc}</span>
                                    </div>
                                </#if>

                                <form id="kc-reset-password-form" action="${url.loginAction}" method="post" class="uc1-form">
                                    <div class="form-group uc1-form-group">
                                        <label for="username" class="uc1-label">
                                            <#if !realm.loginWithEmailAllowed>${msg("username")}<#elseif !realm.registrationEmailAsUsername>${msg("usernameOrEmail")}<#else>${msg("email")}</#if>
                                        </label>
                                        <input type="text" id="username" name="username" class="form-control uc1-input"
                                               autofocus value="${(auth.attemptedUsername!'')}" />
                                    </div>

                                    <div class="form-group uc1-button-group">
                                        <div id="kc-form-buttons" style="display: flex; flex-direction: column; gap: 12px;">
                                            <input class="btn btn-primary btn-block btn-lg uc1-submit-btn"
                                                   type="submit" value="${msg("doSubmit")}"/>
                                        </div>
                                    </div>

                                    <div class="uc1-registration" style="margin-top: 20px;">
                                        <span><a href="${url.loginUrl}" class="uc1-link">&laquo; ${msg("backToLogin")}</a></span>
                                    </div>
                                </form>
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
