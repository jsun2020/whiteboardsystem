# Billing & Admin System Documentation

## 🎯 Overview
Complete billing and admin system with usage tracking, payment processing, and administrative controls.

## ✅ Features Implemented

### 1. **Usage Tracking System**
- **10 Free Uses**: New users get 10 free uses for image processing
- **Usage Counters**: Tracks projects created, images processed, and exports generated
- **Access Control**: Prevents usage beyond limits with helpful error messages
- **Real-time Updates**: Usage indicator in header shows remaining uses

### 2. **Payment System**
- **Pricing Plans**:
  - Monthly: ¥16.5/month
  - Semi-Annual: ¥99/6 months (17% savings)  
  - Annual: ¥198/year (50% savings)
- **QR Code Payment**: Developer's payment QR code for WeChat Pay/Alipay
- **Payment Modal**: Professional payment interface with plan comparison
- **Usage Limit Modal**: Shown when users exceed free uses

### 3. **API Key Alternative**
- **Custom API Settings**: Users can add their own Doubao API key
- **Unlimited Usage**: Custom API key bypasses usage limits
- **Settings Integration**: API key management in user settings

### 4. **Admin Panel** (Developer Only)
- **Admin Detection**: Automatic admin access for admin users
- **System Statistics**: User counts, revenue, subscription stats
- **User Management**: View and edit user subscriptions
- **Payment Management**: QR code display and payment instructions
- **Data Export**: Export system data as CSV

### 5. **Admin Controls**
- **User Subscription Management**: Activate/modify user plans
- **Payment Status Control**: Set payment status (pending/active/expired)
- **Subscription Activation**: Set expiration dates automatically
- **Revenue Tracking**: Monthly revenue calculations

## 🚀 Usage Workflow

### For Regular Users:
1. **Register & Login**: Get 10 free uses
2. **Use Service**: Upload images, process, export
3. **Hit Limit**: See upgrade options when 10 uses exceeded
4. **Choose Option**:
   - Add own API key (free unlimited)
   - Pay for subscription plans
5. **Payment**: Scan QR code, contact developer
6. **Activation**: Developer activates subscription

### For Developers (Admin):
1. **Auto Admin Access**: Admin button appears in header
2. **Monitor System**: View stats, user activity, revenue  
3. **Process Payments**: Customer contacts after payment
4. **Activate Subscriptions**: Use admin panel to activate users
5. **Manage Users**: Edit plans, status, expiration dates

## 🔧 Technical Implementation

### Backend Changes:
- **Upload API**: Added authentication & usage validation
- **Export API**: Added authentication & usage validation  
- **User Model**: Usage tracking methods already existed
- **Admin Endpoints**: Existing admin endpoints in auth.py

### Frontend Changes:
- **Usage Limit Modal**: Professional upgrade prompts
- **Admin Panel**: Complete admin interface
- **Payment Flow**: QR code payment system
- **API Key Settings**: Already existed in settings

### Database:
- **Schema Updated**: All required columns added via migration
- **Usage Tracking**: Increment counters on each operation
- **Admin Users**: Can be created with create_admin.py script

## 📋 Admin Setup Instructions

### 1. Create Admin User:
```bash
python create_admin.py admin@company.com yourpassword123
```

### 2. Login as Admin:
- Login with admin credentials
- Admin button automatically appears in header
- Click "Admin" to access admin panel

### 3. Process Customer Payments:
- Customer pays via QR code
- Customer contacts you with transaction ID
- Use admin panel → "Manage Users" → "Edit Plan"
- Set subscription type and activate

## 🎨 UI/UX Features
- **Professional Design**: Clean, modern interface
- **Responsive**: Works on all devices
- **User Friendly**: Clear upgrade paths and instructions
- **Admin Dashboard**: Comprehensive management tools
- **Real-time Updates**: Usage counters update immediately

## 🔒 Security
- **Authentication Required**: All protected endpoints require login
- **Admin Only**: Admin panel only accessible to admin users
- **User Isolation**: Users can only access their own projects
- **Input Validation**: All forms properly validated

## 💰 Revenue Model
- **Freemium**: 10 free uses to attract users
- **Flexible Plans**: Multiple pricing options
- **API Alternative**: Tech-savvy users can use own API keys
- **Manual Activation**: Developer controls all activations

---

**System is ready for production use!** 🎉

All features are implemented and tested. The billing system provides a smooth user experience while giving developers complete control over subscriptions and payments.