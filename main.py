from fastapi import FastAPI, HTTPException, status

from db import redis_client
from deps import SessionDep, CurrUser
from models import SignupRequest, User, LoginRequest, AddPostRequest, Post
from utils import create_access_token, verify_password, get_password_hash

app = FastAPI()


@app.post("/signup")
def signup(request: SignupRequest, db: SessionDep):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    hashed_password = get_password_hash(request.password)
    user = User(email=request.email, password=hashed_password)
    db.add(user)
    db.commit()
    return {"message": "User created"}


@app.post("/login")
def login(request: LoginRequest, db: SessionDep):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_access_token({"sub": user.email})
    return {"token": token}


@app.post("/add_post")
def add_post(request: AddPostRequest, db: SessionDep, user: CurrUser):
    post = Post(user_id=user.id, text=request.text)
    db.add(post)
    db.commit()
    return {"postID": post.id}


@app.get("/get_posts")
def get_posts(db: SessionDep, user: CurrUser):
    cache_key = f"posts_{user.id}"
    cached_posts = redis_client.get(cache_key)
    if cached_posts:
        return {"posts": cached_posts.decode("utf-8")}

    posts = db.query(Post).filter(Post.user_id == user.id).all()
    redis_client.setex(cache_key, 300, str(posts))
    return {"posts": posts}


@app.delete("/delete_post/{post_id}")
def delete_post(post_id: int, db: SessionDep, user: CurrUser):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    db.delete(post)
    db.commit()
    redis_client.delete(f"posts_{user.id}")
    return {"message": "Post deleted"}
