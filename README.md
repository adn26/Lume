# **Lume - Real-Time Group Chat App** 💬🚀  

Lume is a real-time group chat application built with **Django, WebSockets, HTMX, and AWS**. It allows users to create unique chat groups, send messages instantly, and manage group memberships with permissions.  

This project was initially built by following a tutorial by **[Andreas Jud](https://www.youtube.com/@AndreasJud)**, with additional custom features added by me.  

![Lume Chat App](your-screenshot-url)  

## **🚀 Features**  

- **Real-time messaging** with **WebSockets**  
- **Create & join** chat groups with unique short UIDs  
- **Ban/Unban users** from groups   
- **Notification system** 
- Secure user **authentication** and **authorization**  
- Media & file sharing (Images, Videos, Docs)  
- Modern **HTMX-based UI** for seamless interactions  
- Deployed on **Render** (Amazon S3 for media, Whitenoise for static files)  

## **🛠️ Tech Stack**  

- **Backend:** Django, Django Channels, Django REST Framework  
- **Frontend:** HTMX, Tailwind CSS  
- **Database:** PostgreSQL / SQLite (dev)  
- **WebSockets:** Django Channels, Redis  
- **Storage & Deployment:** AWS (S3, EC2), Whitenoise, Render(For Deployment)

## **📸 Screenshots**  
 <img width="959" alt="public_chat" src="https://github.com/user-attachments/assets/f1237663-26d6-4257-be8c-e5dda1fd6277" />
 
<img width="129" alt="notis" src="https://github.com/user-attachments/assets/122e2901-5193-4aa6-978d-049ca517d0c2" />
<img width="476" alt="edit_profile" src="https://github.com/user-attachments/assets/768901e6-7bc3-4f72-94fd-aa4eee155952" />

<img width="476" alt="create_groupchat" src="https://github.com/user-attachments/assets/c10ecdb6-6fb1-4754-97eb-974f441b6b6c" />
<img width="476" alt="created_chat" src="https://github.com/user-attachments/assets/258917a8-1c67-4ba5-9ffc-1fc44eac82fa" />

## **🚀 Getting Started**  

### **1️⃣ Clone the Repo**  
```bash
git clone https://github.com/adn26/Lume-TheChatApp.git
cd lume-chat
```

### **2️⃣Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3️⃣ Set Up Environment Variables**
Create a .env file and add the following:
```bash
ENVIRONMENT = development # use production when configuring env variables on deployment
SECRET_KEY=your-secret-key  
DEBUG=True  
DATABASE_URL=your-database-url  
REDIS_URL=your-redis-url  
AWS_ACCESS_KEY=your-key  
AWS_SECRET_KEY=your-key 
```

### **4️⃣ Run Migrations**
```bash
python manage.py migrate
```

### **5️⃣ Start the Server**
```bash
python manage.py runserver
```

### **6️⃣ Open in Browser**
Go to http://localhost:8000

## ✨ Custom Features I Added  
- ✅ **Ban/Unban logic** – Group admins can ban/unban users  
- ✅ **Notification logic** – Users receive notifications for new messages  
- ✅ **Improved UI/UX** – Added animations, improved layout  

## 🛠️ Future Improvements  
- ✅ **Voice messaging**  
- ✅ **Push notifications**  
- ✅ **Dark mode**  
- ✅ **AI-powered chat suggestions**  

## 📜 Credits & License  
- Based on a tutorial by **[Andreas Jud](https://www.youtube.com/@ajudmeister)**  
- Custom features and enhancements by **Adnan**  
- Licensed under **MIT License** – use it freely!  

## 🤝 Contributing  
Feel free to submit **PRs** or open **issues**! 🚀  

