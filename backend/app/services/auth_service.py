import hashlib
import hmac
import jwt
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from ..models.user import User, UserRole, AdminLevel, LoginType, Permission, CustomerIntegration, AdminRole
from ..core.config import settings

class AuthService:
    def __init__(self, db: Database):
        self.db = db
        self.users_collection: Collection = db.users
        self.admin_roles_collection: Collection = db.admin_roles
        self.customer_integrations_collection: Collection = db.customer_integrations
        self.sessions_collection: Collection = db.sessions
        
        # JWT 설정
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        # 초기 데이터 설정
        self._init_default_data()
    
    def _init_default_data(self):
        """기본 데이터 초기화"""
        # 기본 관리자 역할 생성
        if not self.admin_roles_collection.find_one({"name": "Super Admin"}):
            super_admin_role = AdminRole(
                name="Super Admin",
                level=AdminLevel.SUPER_ADMIN,
                permissions=[
                    Permission.CHAT_ACCESS, Permission.CHAT_HISTORY,
                    Permission.ANALYSIS_ACCESS, Permission.ANALYSIS_EXPORT,
                    Permission.USER_MANAGEMENT, Permission.SYSTEM_SETTINGS,
                    Permission.COUNSELING_ACCESS, Permission.COUNSELING_MANAGE,
                    Permission.DASHBOARD_VIEW, Permission.REPORTS_VIEW,
                    Permission.REPORTS_EXPORT, Permission.SYSTEM_MONITOR
                ],
                page_access=["dashboard", "counseling_list", "reports", "user_management", "system_monitoring", "settings"],
                customer_access=["*"],
                can_manage_users=True,
                can_manage_roles=True,
                can_export_data=True,
                can_view_reports=True,
                can_monitor_system=True
            )
            self.admin_roles_collection.insert_one(super_admin_role.dict())
        
        # 아름넷 고객사 통합 설정
        if not self.customer_integrations_collection.find_one({"customer_id": "arumnet"}):
            arumnet_integration = CustomerIntegration(
                customer_id="arumnet",
                name="아름넷",
                auth_method="signature",
                secret_key="arumnet_secret_key_2024",  # 실제 운영시에는 환경변수로 관리
                allowed_domains=["arumnet.com", "localhost"],
                auto_login_enabled=True,
                session_timeout=3600,
                max_sessions=5
            )
            self.customer_integrations_collection.insert_one(arumnet_integration.dict())
        
        # 기본 텔리젠 관리자 생성
        if not self.users_collection.find_one({"username": "admin"}):
            admin_user = User(
                username="admin",
                email="admin@telizen.com",
                password_hash=self._hash_password("admin123"),  # 실제 운영시에는 강력한 비밀번호 사용
                role=UserRole.TELIZEN_ADMIN,
                admin_level=AdminLevel.SUPER_ADMIN,
                company="telizen",
                permissions=[
                    Permission.CHAT_ACCESS, Permission.CHAT_HISTORY,
                    Permission.ANALYSIS_ACCESS, Permission.ANALYSIS_EXPORT,
                    Permission.USER_MANAGEMENT, Permission.SYSTEM_SETTINGS,
                    Permission.COUNSELING_ACCESS, Permission.COUNSELING_MANAGE,
                    Permission.DASHBOARD_VIEW, Permission.REPORTS_VIEW,
                    Permission.REPORTS_EXPORT, Permission.SYSTEM_MONITOR
                ]
            )
            self.users_collection.insert_one(admin_user.dict())
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해싱"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """비밀번호 검증"""
        return self._hash_password(password) == hashed
    
    def _create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """JWT 액세스 토큰 생성"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def _verify_signature(self, customer_id: str, user_id: str, timestamp: int, signature: str) -> bool:
        """서명 검증"""
        customer = self.customer_integrations_collection.find_one({"customer_id": customer_id})
        if not customer:
            return False
        
        # 서명 생성
        message = f"{customer_id}{user_id}{timestamp}"
        expected_signature = hmac.new(
            customer["secret_key"].encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def auto_login(self, customer_id: str, user_id: str, user_name: str, 
                   store_id: Optional[str] = None, timestamp: int = None, 
                   signature: str = None, program_version: str = None) -> Dict[str, Any]:
        """자동 로그인"""
        try:
            # 서명 검증
            if not self._verify_signature(customer_id, user_id, timestamp, signature):
                raise ValueError("Invalid signature")
            
            # 타임스탬프 검증 (5분 이내)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:
                raise ValueError("Timestamp expired")
            
            # 사용자 조회 또는 생성
            user = await self.users_collection.find_one({
                "company": customer_id,
                "username": user_id
            })
            
            if not user:
                # 새 사용자 생성
                user = User(
                    username=user_id,
                    role=UserRole.CUSTOMER,
                    company=customer_id,
                    store_id=store_id,
                    login_type=LoginType.AUTO,
                    permissions=[Permission.CHAT_ACCESS, Permission.CHAT_HISTORY]
                )
                await self.users_collection.insert_one(user.dict())
            else:
                # 로그인 시간 업데이트
                await self.users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"last_login_at": datetime.now()}}
                )
            
            # 액세스 토큰 생성
            access_token = self._create_access_token(
                data={"sub": user["id"], "role": user["role"], "company": user["company"]}
            )
            
            # 세션 저장
            session_data = {
                "user_id": user["id"],
                "access_token": access_token,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=1)
            }
            await self.sessions_collection.insert_one(session_data)
            
            return {
                "success": True,
                "access_token": access_token,
                "user_info": {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "company": user["company"],
                    "store_id": user.get("store_id"),
                    "permissions": user["permissions"]
                },
                "expires_in": 3600
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def email_login(self, email: str, password: str) -> Dict[str, Any]:
        """이메일/비밀번호 로그인"""
        try:
            # 사용자 조회 (이메일로)
            user = await self.users_collection.find_one({"email": email})
            
            if not user:
                return {
                    "success": False,
                    "error": "이메일 또는 비밀번호가 올바르지 않습니다."
                }
            
            # 비밀번호 검증
            if not self._verify_password(password, user["password_hash"]):
                return {
                    "success": False,
                    "error": "이메일 또는 비밀번호가 올바르지 않습니다."
                }
            
            # 계정 활성화 확인
            if not user.get("is_active", True):
                return {
                    "success": False,
                    "error": "비활성화된 계정입니다."
                }
            
            # 로그인 시간 업데이트
            await self.users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login_at": datetime.now()}}
            )
            
            # 액세스 토큰 생성
            access_token = self._create_access_token(
                data={"sub": user["id"], "role": user["role"], "company": user["company"]}
            )
            
            # 세션 저장
            session_data = {
                "user_id": user["id"],
                "access_token": access_token,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=1)
            }
            await self.sessions_collection.insert_one(session_data)
            
            return {
                "success": True,
                "access_token": access_token,
                "user_info": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "company": user["company"],
                    "permissions": user["permissions"]
                },
                "expires_in": 3600
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """사용자 회원가입"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"register_user 호출: username={username}, email={email}")
        
        try:
            # 이메일 중복 확인
            existing_user = await self.users_collection.find_one({"email": email})
            logger.info(f"이메일 중복 확인 결과: {existing_user is not None}")
            
            if existing_user:
                logger.warning(f"이메일 중복: {email}")
                return {
                    "success": False,
                    "error": "이미 사용 중인 이메일입니다."
                }
            
            # 사용자명 중복 확인
            existing_username = await self.users_collection.find_one({"username": username})
            logger.info(f"사용자명 중복 확인 결과: {existing_username is not None}")
            
            if existing_username:
                logger.warning(f"사용자명 중복: {username}")
                return {
                    "success": False,
                    "error": "이미 사용 중인 사용자명입니다."
                }
            
            # 새 사용자 생성
            user = User(
                username=username,
                email=email,
                password_hash=self._hash_password(password),
                role=UserRole.CUSTOMER,
                company="telizen",
                permissions=[Permission.CHAT_ACCESS, Permission.CHAT_HISTORY]
            )
            
            logger.info(f"새 사용자 객체 생성: {user.dict()}")
            
            # DB에 저장
            result = await self.users_collection.insert_one(user.dict())
            logger.info(f"DB 저장 결과: {result.inserted_id}")
            
            # 자동 로그인
            login_result = await self.email_login(email, password)
            logger.info(f"자동 로그인 결과: {login_result}")
            return login_result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def manual_login(self, username: str, password: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """수동 로그인"""
        try:
            # 사용자 조회
            query = {"username": username}
            if customer_id:
                query["company"] = customer_id
            
            user = self.users_collection.find_one(query)
            if not user:
                raise ValueError("User not found")
            
            # 비밀번호 검증
            if not self._verify_password(password, user["password_hash"]):
                raise ValueError("Invalid password")
            
            # 계정 활성화 확인
            if not user.get("is_active", True):
                raise ValueError("Account is disabled")
            
            # 로그인 시간 업데이트
            self.users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login_at": datetime.now()}}
            )
            
            # 액세스 토큰 생성
            access_token = self._create_access_token(
                data={"sub": user["id"], "role": user["role"], "company": user["company"]}
            )
            
            # 세션 저장
            session_data = {
                "user_id": user["id"],
                "access_token": access_token,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=1)
            }
            self.sessions_collection.insert_one(session_data)
            
            return {
                "success": True,
                "access_token": access_token,
                "user_info": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user.get("email"),
                    "role": user["role"],
                    "admin_level": user.get("admin_level"),
                    "company": user["company"],
                    "store_id": user.get("store_id"),
                    "permissions": user["permissions"]
                },
                "expires_in": 3600
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰 검증"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                return None
            
            # 세션 확인
            session = self.sessions_collection.find_one({
                "access_token": token,
                "expires_at": {"$gt": datetime.now()}
            })
            
            if not session:
                return None
            
            # 사용자 정보 조회
            user = self.users_collection.find_one({"id": user_id})
            if not user:
                return None
            
            return {
                "user_id": user_id,
                "role": user["role"],
                "company": user["company"],
                "permissions": user["permissions"]
            }
            
        except jwt.PyJWTError:
            return None
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """사용자 권한 조회"""
        user = self.users_collection.find_one({"id": user_id})
        if not user:
            return []
        return user.get("permissions", [])
    
    def check_page_access(self, user_id: str, page_id: str) -> bool:
        """페이지 접근 권한 확인"""
        user = self.users_collection.find_one({"id": user_id})
        if not user:
            return False
        
        # 페이지 권한 확인 로직 구현
        # (PAGE_PERMISSIONS에서 해당 페이지의 권한 요구사항 확인)
        return True  # 임시로 True 반환
    
    def logout(self, token: str) -> bool:
        """로그아웃"""
        try:
            # 세션 삭제
            result = self.sessions_collection.delete_one({"access_token": token})
            return result.deleted_count > 0
        except Exception:
            return False 