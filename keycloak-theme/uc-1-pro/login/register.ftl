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

    <title>Create Account - Unicorn Commander</title>
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
                            <h1 class="uc1-title">Create Your Account</h1>
                            <p class="uc1-subtitle">Free. No credit card required.</p>
                        </header>

                        <div id="kc-content">
                            <div id="kc-content-wrapper">
                                <#if social.providers?? && social.providers?size gt 0>
                                    <div id="kc-social-providers" class="uc1-social-providers">
                                        <h4>Sign up with</h4>
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
                                        <hr/>
                                        <h4 style="text-align: center; color: rgba(255,255,255,0.5); font-weight: normal; font-size: 0.85rem;">or register with email</h4>
                                    </div>
                                </#if>

                                <div id="kc-form">
                                    <div id="kc-form-wrapper">
                                        <form id="kc-register-form" action="${url.registrationAction}" method="post" class="uc1-form">

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
                                                <label for="firstName" class="uc1-label">First name</label>
                                                <input type="text" id="firstName" class="form-control uc1-input" name="firstName"
                                                       value="${(register.formData.firstName!'')}" autocomplete="given-name" />
                                            </div>

                                            <div class="form-group uc1-form-group">
                                                <label for="lastName" class="uc1-label">Last name</label>
                                                <input type="text" id="lastName" class="form-control uc1-input" name="lastName"
                                                       value="${(register.formData.lastName!'')}" autocomplete="family-name" />
                                            </div>

                                            <div class="form-group uc1-form-group">
                                                <label for="email" class="uc1-label">Email</label>
                                                <input type="email" id="email" class="form-control uc1-input" name="email"
                                                       value="${(register.formData.email!'')}" autocomplete="email" autofocus
                                                       aria-invalid="<#if messagesPerField.existsError('email')>true</#if>" />
                                                <#if messagesPerField.existsError('email')>
                                                    <span class="uc1-error" aria-live="polite">
                                                        ${kcSanitize(messagesPerField.getFirstError('email'))?no_esc}
                                                    </span>
                                                </#if>
                                            </div>

                                            <#if !realm.registrationEmailAsUsername>
                                                <div class="form-group uc1-form-group">
                                                    <label for="username" class="uc1-label">Username</label>
                                                    <input type="text" id="username" class="form-control uc1-input" name="username"
                                                           value="${(register.formData.username!'')}" autocomplete="username"
                                                           aria-invalid="<#if messagesPerField.existsError('username')>true</#if>" />
                                                    <#if messagesPerField.existsError('username')>
                                                        <span class="uc1-error" aria-live="polite">
                                                            ${kcSanitize(messagesPerField.getFirstError('username'))?no_esc}
                                                        </span>
                                                    </#if>
                                                </div>
                                            </#if>

                                            <div class="form-group uc1-form-group">
                                                <label for="password" class="uc1-label">Password</label>
                                                <input type="password" id="password" class="form-control uc1-input" name="password"
                                                       autocomplete="new-password"
                                                       aria-invalid="<#if messagesPerField.existsError('password','password-confirm')>true</#if>" />
                                                <#if messagesPerField.existsError('password')>
                                                    <span class="uc1-error" aria-live="polite">
                                                        ${kcSanitize(messagesPerField.getFirstError('password'))?no_esc}
                                                    </span>
                                                </#if>
                                            </div>

                                            <div class="form-group uc1-form-group">
                                                <label for="password-confirm" class="uc1-label">Confirm password</label>
                                                <input type="password" id="password-confirm" class="form-control uc1-input" name="password-confirm"
                                                       autocomplete="new-password"
                                                       aria-invalid="<#if messagesPerField.existsError('password-confirm')>true</#if>" />
                                                <#if messagesPerField.existsError('password-confirm')>
                                                    <span class="uc1-error" aria-live="polite">
                                                        ${kcSanitize(messagesPerField.getFirstError('password-confirm'))?no_esc}
                                                    </span>
                                                </#if>
                                            </div>

                                            <#if recaptchaRequired??>
                                                <div class="form-group">
                                                    <div class="${properties.kcInputWrapperClass!}">
                                                        <div class="g-recaptcha" data-size="compact" data-sitekey="${recaptchaSiteKey}"></div>
                                                    </div>
                                                </div>
                                            </#if>

                                            <div id="kc-form-buttons" class="form-group uc1-button-group">
                                                <input class="btn btn-primary btn-block btn-lg uc1-submit-btn"
                                                       type="submit" value="Create Account"/>
                                            </div>
                                        </form>

                                        <div id="kc-registration" class="uc1-registration">
                                            <span>Already have an account? <a href="${url.loginUrl}" class="uc1-link">Sign in</a></span>
                                        </div>
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
