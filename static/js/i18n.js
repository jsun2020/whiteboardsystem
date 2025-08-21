// Internationalization (i18n) System
class I18n {
    constructor() {
        this.currentLanguage = 'zh-CN'; // Default to Chinese
        this.translations = {};
        this.fallbackLanguage = 'en';
        
        // Load translations
        this.loadTranslations();
        
        // Set initial language from localStorage or default
        const savedLanguage = localStorage.getItem('language') || 'zh-CN';
        this.setLanguage(savedLanguage);
    }

    // Load translation files
    loadTranslations() {
        this.translations = {
            'zh-CN': {
                // Header
                'app.title': '会议白板记录员',
                'header.dashboard': '仪表盘',
                'header.new_project': '新建项目',
                
                // Welcome Section
                'welcome.title': '将您的白板照片转换为结构化的数字内容',
                'welcome.subtitle': '上传白板照片，使用AI分析自动提取文本、表格、行动项和图表。',
                'upload.drag_drop': '拖拽您的白板照片到此处',
                'upload.or': '或',
                'upload.browse': '浏览文件',
                'upload.supported_formats': '支持 JPG, PNG, HEIC, WebP • 单个文件最大 10MB • 最多 5 张图片',
                'upload.take_photo': '拍照',
                'demo.try': '试用演示',
                'demo.description': '查看示例白板的工作原理',
                
                // Features
                'feature.smart_recognition.title': '智能识别',
                'feature.smart_recognition.desc': 'AI驱动的文本、表格和图表提取',
                'feature.multiple_formats.title': '多种格式',
                'feature.multiple_formats.desc': '导出为 Markdown、PowerPoint、思维导图',
                'feature.action_items.title': '行动项',
                'feature.action_items.desc': '自动检测和整理任务',
                'feature.easy_sharing.title': '便捷分享',
                'feature.easy_sharing.desc': '生成可分享的链接并协作',
                
                // Processing Section
                'processing.title': '正在处理您的白板',
                'processing.subtitle': '正在使用AI分析内容...',
                'processing.uploading': '上传中',
                'processing.enhancing': '增强中',
                'processing.analyzing': '分析中',
                'processing.structuring': '结构化中',
                'processing.preparing': '准备上传...',
                'processing.cancel': '取消',
                
                // Results Section
                'results.title': '白板分析完成',
                'results.sections': '个章节',
                'results.action_items': '个行动项',
                'results.tables': '个表格',
                'results.confidence': '置信度',
                'results.original_images': '原始图片',
                'results.regions': '区域',
                'results.zoom': '缩放',
                'results.extracted_content': '提取的内容',
                'results.edit': '编辑',
                'results.copy': '复制',
                'results.structured': '结构化',
                'results.raw_text': '原始文本',
                
                // Export
                'export.markdown': 'Markdown',
                'export.powerpoint': 'PowerPoint',
                'export.mindmap': '思维导图',
                'export.notion': 'Notion',
                'export.confluence': 'Confluence',
                'export.share': '分享',
                'export.save_project': '保存项目',
                
                // Dashboard
                'dashboard.title': '仪表盘',
                'dashboard.close': '关闭',
                'dashboard.total_projects': '项目总数',
                'dashboard.whiteboards_processed': '已处理白板',
                'dashboard.exports_generated': '生成的导出',
                'dashboard.success_rate': '成功率',
                'dashboard.recent_projects': '最近项目',
                
                // Authentication
                'auth.login': '登录',
                'auth.register': '注册',
                'auth.setting': '设置',
                'auth.login_title': '登录您的账户',
                'auth.register_title': '创建您的账户',
                'auth.email': '邮箱',
                'auth.username': '用户名',
                'auth.display_name': '显示名称',
                'auth.password': '密码',
                'auth.confirm_password': '确认密码',
                'auth.create_account': '创建账户',
                'auth.or': '或',
                'auth.no_account': '还没有账户？',
                'auth.register_here': '在此注册',
                'auth.have_account': '已有账户？',
                'auth.login_here': '在此登录',
                'auth.logout': '登出',
                'auth.email_placeholder': '请输入您的邮箱',
                'auth.password_placeholder': '请输入您的密码',
                'auth.username_placeholder': '选择用户名',
                'auth.display_name_placeholder': '您的显示名称',
                'auth.new_password_placeholder': '创建密码',
                'auth.confirm_password_placeholder': '确认您的密码',
                
                // User Menu
                'user.profile': '个人资料',
                'user.usage': '使用情况和计费',
                'user.settings': '设置',

                // Common
                'common.loading': '加载中...',
                'common.processing': '处理中...',
                'common.error': '错误',
                'common.success': '成功',
                'common.cancel': '取消',
                'common.save': '保存',
                'common.close': '关闭',
                'common.edit': '编辑',
                'common.delete': '删除',
                'common.share': '分享',
                'common.export': '导出',
                'common.copy': '复制',
                
                // Language Switcher
                'language.chinese': '中文',
                'language.english': 'English'
            },
            'en': {
                // Header
                'app.title': 'Meeting Whiteboard Scribe',
                'header.dashboard': 'Dashboard',
                'header.new_project': 'New Project',
                
                // Welcome Section
                'welcome.title': 'Transform Your Whiteboard Photos into Structured Digital Content',
                'welcome.subtitle': 'Upload whiteboard photos and automatically extract text, tables, action items, and diagrams using AI-powered analysis.',
                'upload.drag_drop': 'Drag & drop your whiteboard photos',
                'upload.or': 'or',
                'upload.browse': 'browse files',
                'upload.supported_formats': 'Supports JPG, PNG, HEIC, WebP • Max 10MB per image • Up to 5 images',
                'upload.take_photo': 'Take Photo',
                'demo.try': 'Try Demo',
                'demo.description': 'See how it works with sample whiteboard',
                
                // Features
                'feature.smart_recognition.title': 'Smart Recognition',
                'feature.smart_recognition.desc': 'AI-powered text, table, and diagram extraction',
                'feature.multiple_formats.title': 'Multiple Formats',
                'feature.multiple_formats.desc': 'Export to Markdown, PowerPoint, Mind Maps',
                'feature.action_items.title': 'Action Items',
                'feature.action_items.desc': 'Automatically detect and organize tasks',
                'feature.easy_sharing.title': 'Easy Sharing',
                'feature.easy_sharing.desc': 'Generate shareable links and collaborate',
                
                // Processing Section
                'processing.title': 'Processing Your Whiteboard',
                'processing.subtitle': 'Analyzing content with AI...',
                'processing.uploading': 'Uploading',
                'processing.enhancing': 'Enhancing',
                'processing.analyzing': 'Analyzing',
                'processing.structuring': 'Structuring',
                'processing.preparing': 'Preparing for upload...',
                'processing.cancel': 'Cancel',
                
                // Results Section
                'results.title': 'Whiteboard Analysis Complete',
                'results.sections': 'sections',
                'results.action_items': 'action items',
                'results.tables': 'tables',
                'results.confidence': 'confidence',
                'results.original_images': 'Original Images',
                'results.regions': 'Regions',
                'results.zoom': 'Zoom',
                'results.extracted_content': 'Extracted Content',
                'results.edit': 'Edit',
                'results.copy': 'Copy',
                'results.structured': 'Structured',
                'results.raw_text': 'Raw Text',
                
                // Export
                'export.markdown': 'Markdown',
                'export.powerpoint': 'PowerPoint',
                'export.mindmap': 'Mind Map',
                'export.notion': 'Notion',
                'export.confluence': 'Confluence',
                'export.share': 'Share',
                'export.save_project': 'Save Project',
                
                // Dashboard
                'dashboard.title': 'Dashboard',
                'dashboard.close': 'Close',
                'dashboard.total_projects': 'Total Projects',
                'dashboard.whiteboards_processed': 'Whiteboards Processed',
                'dashboard.exports_generated': 'Exports Generated',
                'dashboard.success_rate': 'Success Rate',
                'dashboard.recent_projects': 'Recent Projects',
                
                // Authentication
                'auth.login': 'login',
                'auth.register': 'register',
                'auth.setting': 'setting',
                'auth.login_title': 'Login to Your Account',
                'auth.register_title': 'Create Your Account',
                'auth.email': 'Email',
                'auth.username': 'Username',
                'auth.display_name': 'Display Name',
                'auth.password': 'Password',
                'auth.confirm_password': 'Confirm Password',
                'auth.create_account': 'Create Account',
                'auth.or': 'or',
                'auth.no_account': "Don't have an account?",
                'auth.register_here': 'Register here',
                'auth.have_account': 'Already have an account?',
                'auth.login_here': 'Login here',
                'auth.logout': 'Logout',
                'auth.email_placeholder': 'Enter your email',
                'auth.password_placeholder': 'Enter your password',
                'auth.username_placeholder': 'Choose a username',
                'auth.display_name_placeholder': 'Your display name',
                'auth.new_password_placeholder': 'Create a password',
                'auth.confirm_password_placeholder': 'Confirm your password',
                
                // User Menu
                'user.profile': 'Profile',
                'user.usage': 'Usage & Billing',
                'user.settings': 'Settings',

                // Common
                'common.loading': 'Loading...',
                'common.processing': 'Processing...',
                'common.error': 'Error',
                'common.success': 'Success',
                'common.cancel': 'Cancel',
                'common.save': 'Save',
                'common.close': 'Close',
                'common.edit': 'Edit',
                'common.delete': 'Delete',
                'common.share': 'Share',
                'common.export': 'Export',
                'common.copy': 'Copy',
                
                // Language Switcher
                'language.chinese': '中文',
                'language.english': 'English'
            }
        };
    }

    // Get translation for a key
    t(key, params = {}) {
        let translation = this.translations[this.currentLanguage]?.[key] || 
                         this.translations[this.fallbackLanguage]?.[key] || 
                         key;
        
        // Replace parameters in translation
        Object.keys(params).forEach(param => {
            translation = translation.replace(`{${param}}`, params[param]);
        });
        
        return translation;
    }

    // Set current language
    setLanguage(language) {
        this.currentLanguage = language;
        localStorage.setItem('language', language);
        document.documentElement.lang = language;
        this.translatePage();
        this.updateLanguageSwitcher();
    }

    // Get current language
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    // Translate entire page
    translatePage() {
        // Find all elements with data-i18n attribute
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            // Check if it's an input placeholder
            if (element.hasAttribute('placeholder')) {
                element.placeholder = translation;
            } else if (element.tagName === 'INPUT' && element.type === 'submit') {
                element.value = translation;
            } else {
                element.textContent = translation;
            }
        });

        // Update title
        document.title = this.t('app.title');

        // Trigger custom event for other components to update
        document.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language: this.currentLanguage }
        }));
    }

    // Update language switcher UI
    updateLanguageSwitcher() {
        const switcher = document.getElementById('languageSwitcher');
        if (switcher) {
            const currentLangText = this.currentLanguage === 'zh-CN' ? '中文' : 'English';
            const flagIcon = this.currentLanguage === 'zh-CN' ? '🇨🇳' : '🇺🇸';
            switcher.innerHTML = `<span class="flag">${flagIcon}</span> ${currentLangText}`;
        }
    }

    // Toggle between languages
    toggleLanguage() {
        const newLanguage = this.currentLanguage === 'zh-CN' ? 'en' : 'zh-CN';
        this.setLanguage(newLanguage);
    }
}

// Initialize i18n system
window.i18n = new I18n();

// Export for other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = I18n;
}