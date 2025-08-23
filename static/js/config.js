// Payment and Contact Configuration
window.PAYMENT_CONFIG = {
    // Contact Information - UPDATE THESE WITH YOUR DETAILS
    contact: {
        email: 'jsun2016@live.com',
        wechat: 'your_wechat_id',
        phone: '+86-xxx-xxxx-xxxx', // Optional
    },
    
    // Payment Plans
    plans: {
        monthly: {
            price: 16.5,
            currency: 'CNY',
            duration: '1 month',
            savings: null
        },
        semi_annual: {
            price: 99,
            currency: 'CNY', 
            duration: '6 months',
            savings: '17% savings'
        },
        annual: {
            price: 198,
            currency: 'CNY',
            duration: '12 months', 
            savings: '50% savings'
        }
    },
    
    // QR Code Settings
    qrCode: {
        path: '/static/assets/images/payment-qr.png',
        fallbackText: 'Please add your QR code image'
    },
    
    // Payment Instructions
    instructions: [
        'Scan QR code with WeChat Pay or Alipay',
        'Enter the exact amount shown above',
        'Complete the payment',
        'Screenshot the payment confirmation',
        'Contact support with transaction details'
    ]
};

// Helper function to get contact info
window.getContactInfo = function() {
    return window.PAYMENT_CONFIG.contact;
};

// Helper function to get payment plan info
window.getPaymentPlan = function(planType) {
    return window.PAYMENT_CONFIG.plans[planType];
};