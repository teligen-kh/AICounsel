from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from ...services.auth_service import AuthService
from ...core.database import get_database
from ...models.user import UserRole, Permission

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# 요청 모델
class AutoLoginRequest(BaseModel):
    customer_id: str
    user_id: str
    user_name: str
    store_id: Optional[str] = None
    timestamp: int
    signature: str
    program_version: Optional[str] = None

class ManualLoginRequest(BaseModel):
    username: str
    password: str
    customer_id: Optional[str] = None

class RegisterRequest(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    role: UserRole = UserRole.CUSTOMER
    company: str = "telizen"

# 응답 모델
class LoginResponse(BaseModel):
    success: bool
    access_token: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None
    expires_in: Optional[int] = None
    error: Optional[str] = None

class UserInfoResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: UserRole
    admin_level: Optional[str] = None
    company: str
    store_id: Optional[str] = None
    permissions: list[Permission]
    last_login_at: Optional[datetime] = None

# 의존성
def get_auth_service():
    db = get_database()
    return AuthService(db)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                    auth_service: AuthService = Depends(get_auth_service)) -> Dict[str, Any]:
    """현재 사용자 정보 조회"""
    token = credentials.credentials
    user_info = auth_service.verify_token(token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_info

# API 엔드포인트
@router.post("/auto-login", response_model=LoginResponse)
async def auto_login(
    request: AutoLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """자동 로그인 API"""
    result = auth_service.auto_login(
        customer_id=request.customer_id,
        user_id=request.user_id,
        user_name=request.user_name,
        store_id=request.store_id,
        timestamp=request.timestamp,
        signature=request.signature,
        program_version=request.program_version
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"]
        )
    
    return result

@router.post("/login", response_model=LoginResponse)
async def manual_login(
    request: ManualLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """수동 로그인 API"""
    result = auth_service.manual_login(
        username=request.username,
        password=request.password,
        customer_id=request.customer_id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"]
        )
    
    return result

@router.post("/register", response_model=LoginResponse)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """회원가입 API"""
    # 간단한 회원가입 구현 (실제로는 더 복잡한 검증 필요)
    try:
        # 사용자 생성
        from ...models.user import User, AdminLevel
        from datetime import datetime
        
        user = User(
            username=request.username,
            email=request.email,
            password_hash=auth_service._hash_password(request.password),
            role=request.role,
            company=request.company,
            permissions=[Permission.CHAT_ACCESS, Permission.CHAT_HISTORY]
        )
        
        # DB에 저장
        auth_service.users_collection.insert_one(user.dict())
        
        # 자동 로그인
        result = auth_service.manual_login(
            username=request.username,
            password=request.password,
            customer_id=request.company
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """현재 사용자 정보 조회"""
    user_id = current_user["user_id"]
    user = auth_service.users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserInfoResponse(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        role=user["role"],
        admin_level=user.get("admin_level"),
        company=user["company"],
        store_id=user.get("store_id"),
        permissions=user["permissions"],
        last_login_at=user.get("last_login_at")
    )

@router.get("/permissions")
async def get_user_permissions(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """사용자 권한 조회"""
    user_id = current_user["user_id"]
    permissions = auth_service.get_user_permissions(user_id)
    
    return {
        "permissions": permissions,
        "user_id": user_id
    }

@router.get("/pages")
async def get_accessible_pages(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """접근 가능한 페이지 목록 조회"""
    user_id = current_user["user_id"]
    
    # 페이지 권한 확인 로직 (임시)
    accessible_pages = [
        "dashboard",
        "chat",
        "analysis",
        "list"
    ]
    
    return {
        "accessible_pages": accessible_pages,
        "user_id": user_id
    }

@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """로그아웃"""
    token = credentials.credentials
    success = auth_service.logout(token)
    
    if success:
        return {"message": "Successfully logged out"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed"
        )

# 관리자용 API
@router.get("/admin/users")
async def get_users(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """사용자 목록 조회 (관리자용)"""
    # 권한 확인
    if Permission.USER_MANAGEMENT not in current_user["permissions"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    users = list(auth_service.users_collection.find({}, {"password_hash": 0}))
    return {"users": users}

@router.get("/admin/roles")
async def get_admin_roles(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """관리자 역할 목록 조회"""
    # 권한 확인
    if Permission.USER_MANAGEMENT not in current_user["permissions"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    roles = list(auth_service.admin_roles_collection.find())
    return {"roles": roles} 