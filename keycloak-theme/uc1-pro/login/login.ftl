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
                                <img src="${url.resourcesPath}/img/colonel-logo.png" alt="The Colonel Logo" class="uc1-logo" onerror="this.style.display='none'" />
                            </div>
                            <h1 class="uc1-title">Welcome to Unicorn Commander</h1>
                            <p class="uc1-subtitle">UC-1 Pro Operations Center</p>
                        </header>

                        <div id="kc-content">
                            <div id="kc-content-wrapper">
                                <#if realm.password && social.providers??>
                                    <div id="kc-social-providers" class="uc1-social-providers">
                                        <hr/>
                                        <h4>${msg("identity-provider-login-label")}</h4>
                                        <ul class="uc1-social-links">
                                            <#list social.providers as p>
                                                <li>
                                                    <a id="social-${p.alias}" class="uc1-social-link ${p.providerId}"
                                                       href="${p.loginUrl}">
                                                        <span>${p.displayName!}</span>
                                                    </a>
                                                </li>
                                            </#list>
                                        </ul>
                                    </div>
                                </#if>

                                <div id="kc-form">
                                    <div id="kc-form-wrapper">
                                        <#if realm.password>
                                            <form id="kc-form-login" onsubmit="login.disabled = true; return true;"
                                                  action="${url.loginAction}" method="post" class="uc1-form">

                                                <#if message?has_content && (message.type != 'warning' || !isAppInitiatedAction??)>
                                                    <div class="alert alert-${message.type} uc1-alert">
                                                        <#if message.type = 'success'><span class="pficon pficon-ok"></span></#if>
                                                        <#if message.type = 'warning'><span class="pficon pficon-warning-triangle-o"></span></#if>
                                                        <#if message.type = 'error'><span class="pficon pficon-error-circle-o"></span></#if>
                                                        <#if message.type = 'info'><span class="pficon pficon-info"></span></#if>
                                                        <span class="kc-feedback-text">${kcSanitize(message.summary)?no_esc}</span>
                                                    </div>
                                                </#if>

                                                <div class="form-group uc1-form-group">
                                                    <label for="username" class="uc1-label">
                                                        <#if !realm.loginWithEmailAllowed>${msg("username")}<#elseif !realm.registrationEmailAsUsername>${msg("usernameOrEmail")}<#else>${msg("email")}</#if>
                                                    </label>

                                                    <#if usernameEditDisabled??>
                                                        <input tabindex="1" id="username" class="form-control uc1-input" name="username"
                                                               value="${(login.username!'')}" type="text" disabled />
                                                    <#else>
                                                        <input tabindex="1" id="username" class="form-control uc1-input" name="username"
                                                               value="${(login.username!'')}" type="text" autofocus autocomplete="off"
                                                               aria-invalid="<#if messagesPerField.existsError('username','password')>true</#if>" />

                                                        <#if messagesPerField.existsError('username','password')>
                                                            <span id="input-error" class="uc1-error" aria-live="polite">
                                                                ${kcSanitize(messagesPerField.getFirstError('username','password'))?no_esc}
                                                            </span>
                                                        </#if>
                                                    </#if>
                                                </div>

                                                <div class="form-group uc1-form-group">
                                                    <label for="password" class="uc1-label">${msg("password")}</label>
                                                    <input tabindex="2" id="password" class="form-control uc1-input" name="password"
                                                           type="password" autocomplete="off"
                                                           aria-invalid="<#if messagesPerField.existsError('username','password')>true</#if>" />
                                                </div>

                                                <div class="form-group login-pf-settings uc1-settings">
                                                    <div class="uc1-checkbox-wrapper">
                                                        <#if realm.rememberMe && !usernameEditDisabled??>
                                                            <div class="checkbox">
                                                                <label class="uc1-checkbox-label">
                                                                    <#if login.rememberMe??>
                                                                        <input tabindex="3" id="rememberMe" name="rememberMe" type="checkbox" checked> ${msg("rememberMe")}
                                                                    <#else>
                                                                        <input tabindex="3" id="rememberMe" name="rememberMe" type="checkbox"> ${msg("rememberMe")}
                                                                    </#if>
                                                                </label>
                                                            </div>
                                                        </#if>
                                                    </div>
                                                    <div class="uc1-forgot-password">
                                                        <#if realm.resetPasswordAllowed>
                                                            <span><a tabindex="5" href="${url.loginResetCredentialsUrl}" class="uc1-link">${msg("doForgotPassword")}</a></span>
                                                        </#if>
                                                    </div>
                                                </div>

                                                <div id="kc-form-buttons" class="form-group uc1-button-group">
                                                    <input type="hidden" id="id-hidden-input" name="credentialId"
                                                           <#if auth.selectedCredential?has_content>value="${auth.selectedCredential}"</#if>/>
                                                    <input tabindex="4" class="btn btn-primary btn-block btn-lg uc1-submit-btn"
                                                           name="login" id="kc-login" type="submit" value="${msg("doLogIn")}"/>
                                                </div>
                                            </form>
                                        </#if>

                                        <#if realm.password && realm.registrationAllowed && !registrationDisabled??>
                                            <div id="kc-registration" class="uc1-registration">
                                                <span>${msg("noAccount")} <a tabindex="6" href="${url.registrationUrl}" class="uc1-link">${msg("doRegister")}</a></span>
                                            </div>
                                        </#if>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <footer class="uc1-footer">
                            <p>&copy; 2025 Magic Unicorn Unconventional Technology & Stuff Inc</p>
                        </footer>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
