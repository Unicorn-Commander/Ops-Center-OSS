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

    <title>${msg("loginProfileTitle")}</title>
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
                            <h1 class="uc1-title">Update Profile</h1>
                            <p class="uc1-subtitle">Secure sign-in for all services</p>
                        </header>

                        <div id="kc-content">
                            <div id="kc-content-wrapper">
                                <div id="kc-form">
                                    <div id="kc-form-wrapper">
                                        <form id="kc-update-profile-form" action="${url.loginAction}" method="post" class="uc1-form">

                                            <#if message?has_content && (message.type != 'warning' || !isAppInitiatedAction??)>
                                                <div class="alert alert-${message.type} uc1-alert">
                                                    <#if message.type = 'success'><span class="pficon pficon-ok"></span></#if>
                                                    <#if message.type = 'warning'><span class="pficon pficon-warning-triangle-o"></span></#if>
                                                    <#if message.type = 'error'><span class="pficon pficon-error-circle-o"></span></#if>
                                                    <#if message.type = 'info'><span class="pficon pficon-info"></span></#if>
                                                    <span class="kc-feedback-text">${kcSanitize(message.summary)?no_esc}</span>
                                                </div>
                                            </#if>

                                            <#if user.editUsernameAllowed>
                                                <div class="form-group uc1-form-group">
                                                    <label for="username" class="uc1-label">${msg("username")}</label>
                                                    <input tabindex="1" type="text" id="username" name="username"
                                                           value="${(user.username!'')}"
                                                           class="form-control uc1-input"
                                                           aria-invalid="<#if messagesPerField.existsError('username')>true</#if>" />
                                                    <#if messagesPerField.existsError('username')>
                                                        <span id="input-error-username" class="uc1-error" aria-live="polite">
                                                            ${kcSanitize(messagesPerField.get('username'))?no_esc}
                                                        </span>
                                                    </#if>
                                                </div>
                                            </#if>

                                            <div class="form-group uc1-form-group">
                                                <label for="email" class="uc1-label">${msg("email")}</label>
                                                <input tabindex="2" type="text" id="email" name="email"
                                                       value="${(user.email!'')}"
                                                       class="form-control uc1-input" autofocus
                                                       aria-invalid="<#if messagesPerField.existsError('email')>true</#if>" />
                                                <#if messagesPerField.existsError('email')>
                                                    <span id="input-error-email" class="uc1-error" aria-live="polite">
                                                        ${kcSanitize(messagesPerField.get('email'))?no_esc}
                                                    </span>
                                                </#if>
                                            </div>

                                            <div class="form-group uc1-form-group">
                                                <label for="firstName" class="uc1-label">${msg("firstName")}</label>
                                                <input tabindex="3" type="text" id="firstName" name="firstName"
                                                       value="${(user.firstName!'')}"
                                                       class="form-control uc1-input"
                                                       aria-invalid="<#if messagesPerField.existsError('firstName')>true</#if>" />
                                                <#if messagesPerField.existsError('firstName')>
                                                    <span id="input-error-firstName" class="uc1-error" aria-live="polite">
                                                        ${kcSanitize(messagesPerField.get('firstName'))?no_esc}
                                                    </span>
                                                </#if>
                                            </div>

                                            <div class="form-group uc1-form-group">
                                                <label for="lastName" class="uc1-label">${msg("lastName")}</label>
                                                <input tabindex="4" type="text" id="lastName" name="lastName"
                                                       value="${(user.lastName!'')}"
                                                       class="form-control uc1-input"
                                                       aria-invalid="<#if messagesPerField.existsError('lastName')>true</#if>" />
                                                <#if messagesPerField.existsError('lastName')>
                                                    <span id="input-error-lastName" class="uc1-error" aria-live="polite">
                                                        ${kcSanitize(messagesPerField.get('lastName'))?no_esc}
                                                    </span>
                                                </#if>
                                            </div>

                                            <div class="form-group uc1-form-group">
                                                <div id="kc-form-options" class="uc1-settings">
                                                    <div></div>
                                                </div>

                                                <div id="kc-form-buttons" class="uc1-button-group">
                                                    <#if isAppInitiatedAction??>
                                                        <input tabindex="5" class="btn btn-primary btn-block btn-lg uc1-submit-btn"
                                                               type="submit" value="${msg("doSubmit")}" />
                                                        <button tabindex="6" class="btn btn-default btn-block btn-lg uc1-submit-btn"
                                                                style="margin-top: 10px; background: rgba(255,255,255,0.08) !important;"
                                                                type="submit" name="cancel-aia" value="true">${msg("doCancel")}</button>
                                                    <#else>
                                                        <input tabindex="5" class="btn btn-primary btn-block btn-lg uc1-submit-btn"
                                                               type="submit" value="${msg("doSubmit")}" />
                                                    </#if>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
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
