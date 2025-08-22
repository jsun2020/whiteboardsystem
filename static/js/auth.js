// Authentication Management
class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.user = null;
        this.init();
    }

    async init() {
        if (this.token) {
            await this.loadUserProfile();
        }
        this.updateUI();
    }

    async loadUserProfile() {
        try {
            const response = await fetch('/api/auth/profile', {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.user = data.user;
                return true;
            } else {
                this.logout();
                return false;
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
            this.logout();
            return false;
        }
    }

    updateUI() {
        const guestActions = document.getElementById('guestActions');
        const userActions = document.getElementById('userActions');
        const userDisplayName = document.getElementById('userDisplayName');
        const usageCount = document.getElementById('usageCount');
        const usageIndicator = document.getElementById('usageIndicator');

        if (this.user) {
            // Show user actions, hide guest actions
            if (guestActions) guestActions.style.display = 'none';
            if (userActions) userActions.style.display = 'flex';
            if (userDisplayName) userDisplayName.textContent = this.user.display_name || this.user.username || 'User';
            
            // Update usage indicator
            if (usageCount && this.user) {
                const remainingUses = Math.max(0, 10 - (this.user.free_uses_count || 0));
                usageCount.textContent = this.user.can_use_service ? 
                    (this.user.subscription_type !== 'free' ? '∞' : remainingUses) : '0';
            }
            
            // Add warning/danger classes based on usage
            if (usageIndicator && this.user) {
                usageIndicator.className = 'usage-indicator';
                const remainingUses = Math.max(0, 10 - (this.user.free_uses_count || 0));
                if (!this.user.can_use_service) {
                    usageIndicator.classList.add('danger');
                } else if (remainingUses <= 3 && this.user.subscription_type === 'free') {
                    usageIndicator.classList.add('warning');
                }
            }
        } else {
            // Show guest actions, hide user actions
            if (guestActions) guestActions.style.display = 'flex';
            if (userActions) userActions.style.display = 'none';
        }
    }

    async login(email, password) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.token = data.token;
                this.user = data.user;
                localStorage.setItem('auth_token', this.token);
                this.updateUI();
                return { success: true, message: data.message };
            } else {
                return { success: false, message: data.error };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, message: 'Network error. Please try again.' };
        }
    }

    async register(userData) {
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (response.ok) {
                this.token = data.token;
                this.user = data.user;
                localStorage.setItem('auth_token', this.token);
                this.updateUI();
                return { success: true, message: data.message };
            } else {
                return { success: false, message: data.error };
            }
        } catch (error) {
            console.error('Registration error:', error);
            return { success: false, message: 'Network error. Please try again.' };
        }
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
        this.updateUI();
    }

    isAuthenticated() {
        return !!this.user;
    }

    canUseService() {
        return !this.user || this.user.can_use_service;
    }

    getAuthHeaders() {
        return this.token ? {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        } : {
            'Content-Type': 'application/json'
        };
    }
}

// Global auth manager instance
const authManager = new AuthManager();

// Modal Functions
function showLoginModal() {
    document.getElementById('loginModalOverlay').style.display = 'flex';
    document.getElementById('loginEmail').focus();
}

function closeLoginModal() {
    document.getElementById('loginModalOverlay').style.display = 'none';
    document.getElementById('loginForm').reset();
}

function showRegisterModal() {
    document.getElementById('registerModalOverlay').style.display = 'flex';
    document.getElementById('registerEmail').focus();
}

function closeRegisterModal() {
    document.getElementById('registerModalOverlay').style.display = 'none';
    document.getElementById('registerForm').reset();
}

function switchToRegister() {
    closeLoginModal();
    showRegisterModal();
}

function switchToLogin() {
    closeRegisterModal();
    showLoginModal();
}

// Form Handlers
async function handleLogin(event) {
    event.preventDefault();
    
    const form = event.target;
    const email = form.email.value;
    const password = form.password.value;
    const submitBtn = document.getElementById('loginBtn');
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Logging in...</span>';
    
    const result = await authManager.login(email, password);
    
    
    if (result && result.success === true) {
        // Use setTimeout to ensure modal closes properly
        setTimeout(() => {
            closeLoginModal();
        }, 100);
        showToast('Login successful!', 'success');
    } else {
        showToast(result ? result.message : 'Login failed', 'error');
    }
    
    // Reset button state
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> <span data-i18n="auth.login">Login</span>';
}

async function handleRegister(event) {
    event.preventDefault();
    
    const form = event.target;
    const email = form.email.value;
    const username = form.username.value;
    const displayName = form.display_name.value;
    const password = form.password.value;
    const confirmPassword = form.confirm_password.value;
    const submitBtn = document.getElementById('registerBtn');
    
    // Validate password confirmation
    if (password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Creating Account...</span>';
    
    const result = await authManager.register({
        email,
        username: username || email.split('@')[0],
        display_name: displayName,
        password,
        language: (typeof i18n !== 'undefined' && i18n.currentLanguage) || 'en'
    });
    
    
    if (result && result.success === true) {
        // Use setTimeout to ensure modal closes properly
        setTimeout(() => {
            closeRegisterModal();
        }, 100);
        showToast('Account created successfully!', 'success');
    } else {
        showToast(result ? result.message : 'Registration failed', 'error');
    }
    
    // Reset button state
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> <span data-i18n="auth.create_account">Create Account</span>';
}

function handleLogout() {
    authManager.logout();
    hideUserMenu();
    showToast('Logged out successfully', 'success');
}

// User Menu Functions
function showUserMenu() {
    const dropdown = document.getElementById('userMenuDropdown');
    const isVisible = dropdown.style.display === 'block';
    
    if (isVisible) {
        hideUserMenu();
    } else {
        dropdown.style.display = 'block';
        
        // Position dropdown relative to user info
        const userInfo = document.querySelector('.user-info');
        const rect = userInfo.getBoundingClientRect();
        dropdown.style.top = rect.bottom + 5 + 'px';
        dropdown.style.right = (window.innerWidth - rect.right) + 'px';
    }
}

function hideUserMenu() {
    document.getElementById('userMenuDropdown').style.display = 'none';
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const userMenu = document.getElementById('userMenuDropdown');
    const userInfo = document.querySelector('.user-info');
    
    if (userMenu && !userMenu.contains(event.target) && !userInfo.contains(event.target)) {
        hideUserMenu();
    }
});

// Profile and Settings Modals (to be implemented)
function showProfileModal() {
    hideUserMenu();
    // TODO: Implement profile modal
    console.log('Show profile modal');
}

function showUsageModal() {
    hideUserMenu();
    // TODO: Implement usage/billing modal
    showPaymentModal();
}

function showSettingsModal() {
    const settingsModalBody = `
        <div class="settings-container">
            <div class="settings-tabs">
                <button class="tab-btn active" onclick="switchSettingsTab('profile')">Profile</button>
                <button class="tab-btn" onclick="switchSettingsTab('api')">API Keys</button>
                <button class="tab-btn" onclick="switchSettingsTab('billing')">Billing</button>
            </div>
            <div class="settings-content" id="settingsContent">
                <div id="profileSettings" class="settings-panel active">
                    <h4>Profile Settings</h4>
                    <div class="form-group">
                        <label>Display Name</label>
                        <input type="text" id="settingsDisplayName" value="${authManager.user?.display_name || ''}">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" id="settingsEmail" value="${authManager.user?.email || ''}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Language</label>
                        <select id="settingsLanguage">
                            <option value="en" ${i18n.currentLanguage === 'en' ? 'selected' : ''}>English</option>
                            <option value="zh-CN" ${i18n.currentLanguage === 'zh-CN' ? 'selected' : ''}>中文</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" onclick="saveProfileSettings()">Save Profile</button>
                </div>
                <div id="apiSettings" class="settings-panel">
                    <h4>API Key Settings</h4>
                    <p>Use your own API key to access unlimited service</p>
                    <div class="form-group">
                        <label>Doubao API Key</label>
                        <input type="password" id="settingsApiKey" placeholder="Enter your API key">
                    </div>
                    <div class="form-group">
                        <label>API Endpoint (optional)</label>
                        <input type="url" id="settingsApiEndpoint" placeholder="https://ark.cn-beijing.volces.com/api/v3">
                    </div>
                    <button class="btn btn-primary" onclick="saveApiSettings()">Save API Key</button>
                </div>
                <div id="billingSettings" class="settings-panel">
                    <h4>Usage & Billing</h4>
                    <div class="usage-stats">
                        <div class="stat-item">
                            <span class="stat-label">Plan:</span>
                            <span class="stat-value">${authManager.user?.subscription_type || 'Free'}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Remaining Uses:</span>
                            <span class="stat-value">${authManager.user?.can_use_service ? 
                                (authManager.user?.subscription_type !== 'free' ? '∞' : 
                                Math.max(0, 10 - (authManager.user?.free_uses_count || 0))) : '0'}</span>
                        </div>
                    </div>
                    <button class="btn btn-primary" onclick="showPaymentModal(); closeModal()">Upgrade Plan</button>
                </div>
            </div>
            <div class="settings-footer">
                <button class="btn btn-outline" onclick="handleLogout(); closeModal()">Logout</button>
            </div>
        </div>
    `;
    
    showModal('Settings', settingsModalBody);
}

// Settings Modal Helper Functions
function switchSettingsTab(tabName) {
    // Remove active class from all tabs and panels
    document.querySelectorAll('.settings-tabs .tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.settings-panel').forEach(panel => panel.classList.remove('active'));
    
    // Add active class to selected tab and panel
    document.querySelector(`[onclick="switchSettingsTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`${tabName}Settings`).classList.add('active');
}

async function saveProfileSettings() {
    const displayName = document.getElementById('settingsDisplayName').value;
    const language = document.getElementById('settingsLanguage').value;
    
    try {
        const response = await fetch('/api/auth/profile', {
            method: 'PUT',
            headers: authManager.getAuthHeaders(),
            body: JSON.stringify({
                display_name: displayName,
                language: language
            })
        });
        
        if (response.ok) {
            await authManager.loadUserProfile();
            authManager.updateUI();
            i18n.setLanguage(language);
            showToast('Profile updated successfully!', 'success');
        } else {
            showToast('Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showToast('Error updating profile', 'error');
    }
}

async function saveApiSettings() {
    const apiKey = document.getElementById('settingsApiKey').value;
    const apiEndpoint = document.getElementById('settingsApiEndpoint').value;
    
    if (!apiKey) {
        showToast('Please enter an API key', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/profile', {
            method: 'PUT',
            headers: authManager.getAuthHeaders(),
            body: JSON.stringify({
                custom_api_key: apiKey,
                custom_api_endpoint: apiEndpoint
            })
        });
        
        if (response.ok) {
            await authManager.loadUserProfile();
            authManager.updateUI();
            showToast('API key saved successfully!', 'success');
        } else {
            showToast('Failed to save API key', 'error');
        }
    } catch (error) {
        console.error('Error saving API key:', error);
        showToast('Error saving API key', 'error');
    }
}

// Payment Modal Functions
function showPaymentModal() {
    const modalBody = `
        <div class="payment-plans">
            <h4>Choose Your Plan</h4>
            <div class="plans-grid">
                <div class="plan-card">
                    <h5>Monthly Plan</h5>
                    <div class="price">¥16.5<span>/month</span></div>
                    <ul class="features">
                        <li>Unlimited usage</li>
                        <li>All export formats</li>
                        <li>Priority support</li>
                    </ul>
                    <button class="btn btn-primary" onclick="initiatePayment('monthly')">Select Plan</button>
                </div>
                <div class="plan-card featured">
                    <div class="badge">Best Value</div>
                    <h5>Semi-Annual Plan</h5>
                    <div class="price">¥99<span>/6 months</span></div>
                    <div class="savings">Save 17%</div>
                    <ul class="features">
                        <li>Unlimited usage</li>
                        <li>All export formats</li>
                        <li>Priority support</li>
                        <li>17% savings</li>
                    </ul>
                    <button class="btn btn-primary" onclick="initiatePayment('semi_annual')">Select Plan</button>
                </div>
                <div class="plan-card">
                    <h5>Annual Plan</h5>
                    <div class="price">¥198<span>/year</span></div>
                    <div class="savings">Save 50%</div>
                    <ul class="features">
                        <li>Unlimited usage</li>
                        <li>All export formats</li>
                        <li>Priority support</li>
                        <li>50% savings</li>
                    </ul>
                    <button class="btn btn-primary" onclick="initiatePayment('annual')">Select Plan</button>
                </div>
            </div>
            <div class="custom-api-section">
                <h5>Or use your own API key for free</h5>
                <p>Provide your own Doubao API key to use the service without limits</p>
                <button class="btn btn-outline" onclick="showApiKeyModal()">Add API Key</button>
            </div>
        </div>
    `;
    
    showModal('Choose Your Plan', modalBody);
}

function initiatePayment(planType) {
    const qrCodeModalBody = `
        <div class="payment-qr">
            <h4>Payment Instructions</h4>
            <p>Please scan the QR code below to make payment:</p>
            <div class="qr-container">
                <img src="/static/assets/images/payment-qr.png" alt="Payment QR Code" class="qr-code">
            </div>
            <div class="payment-info">
                <p><strong>Plan:</strong> ${planType === 'monthly' ? 'Monthly (¥16.5)' : 
                    planType === 'semi_annual' ? 'Semi-Annual (¥99)' : 'Annual (¥198)'}</p>
                <p><strong>Payment Method:</strong> WeChat Pay / Alipay</p>
                <p class="payment-note">After payment, please contact support with your transaction ID to activate your subscription.</p>
            </div>
            <div class="payment-contact">
                <p><strong>Contact Developer:</strong></p>
                <p>Email: developer@example.com</p>
                <p>WeChat: developer_wechat</p>
            </div>
        </div>
    `;
    
    showModal('Complete Payment', qrCodeModalBody);
}

function showApiKeyModal() {
    const apiKeyModalBody = `
        <div class="api-key-form">
            <h4>Add Your Doubao API Key</h4>
            <p>Enter your Doubao API key to use the service with your own quota:</p>
            <form onsubmit="saveApiKey(event)">
                <div class="form-group">
                    <label for="apiKey">Doubao API Key</label>
                    <input type="password" id="apiKey" name="apiKey" required 
                           placeholder="Enter your Doubao API key">
                </div>
                <div class="form-group">
                    <label for="apiEndpoint">API Endpoint (optional)</label>
                    <input type="url" id="apiEndpoint" name="apiEndpoint" 
                           placeholder="https://ark.cn-beijing.volces.com/api/v3">
                </div>
                <button type="submit" class="btn btn-primary">Save API Key</button>
            </form>
        </div>
    `;
    
    showModal('API Key Settings', apiKeyModalBody);
}

async function saveApiKey(event) {
    event.preventDefault();
    
    const form = event.target;
    const apiKey = form.apiKey.value;
    const apiEndpoint = form.apiEndpoint.value;
    
    try {
        const response = await fetch('/api/auth/profile', {
            method: 'PUT',
            headers: authManager.getAuthHeaders(),
            body: JSON.stringify({
                custom_api_key: apiKey,
                custom_api_endpoint: apiEndpoint
            })
        });
        
        if (response.ok) {
            await authManager.loadUserProfile();
            authManager.updateUI();
            closeModal();
            showToast('API key saved successfully!', 'success');
        } else {
            showToast('Failed to save API key', 'error');
        }
    } catch (error) {
        console.error('Error saving API key:', error);
        showToast('Error saving API key', 'error');
    }
}

// Export auth manager for use in other scripts
window.authManager = authManager;