"""
LDAPS Authentication Handler
Handles LDAP over SSL authentication for Intertech users
"""

import ssl
import logging
from typing import Optional, Dict, Any
from ldap3 import Server, Connection, Tls, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError

logger = logging.getLogger(__name__)

class LDAPSConfig:
    """LDAP Configuration - Will be set via environment variables"""
    # These are generic defaults - can be configured later
    SERVER_HOST = "ldap.example.com"
    SERVER_PORT = 636
    USE_SSL = True
    BASE_DN = "dc=example,dc=com"
    USER_SEARCH_BASE = "ou=users,dc=example,dc=com"
    USER_SEARCH_FILTER = "(uid={username})"
    BIND_DN_TEMPLATE = "uid={username},ou=users,dc=example,dc=com"
    # For testing/development - set to False in production with valid certificates
    VALIDATE_CERT = False  

class LDAPSHandler:
    """LDAPS Authentication Handler"""
    
    def __init__(self, config: Optional[LDAPSConfig] = None):
        self.config = config or LDAPSConfig()
        self.server = None
        self.tls = None
        self._setup_tls()
        self._setup_server()
    
    def _setup_tls(self):
        """Configure TLS/SSL parameters for secure LDAP connection"""
        try:
            if self.config.VALIDATE_CERT:
                # Production: validate certificates
                self.tls = Tls(
                    validate=ssl.CERT_REQUIRED,
                    version=ssl.PROTOCOL_TLSv1_2
                )
            else:
                # Development: no certificate validation
                self.tls = Tls(
                    validate=ssl.CERT_NONE,
                    version=ssl.PROTOCOL_TLSv1_2
                )
            logger.info("TLS configuration completed")
        except Exception as e:
            logger.error(f"TLS configuration error: {str(e)}")
            raise
    
    def _setup_server(self):
        """Initialize LDAP server connection parameters"""
        try:
            self.server = Server(
                host=self.config.SERVER_HOST,
                port=self.config.SERVER_PORT,
                use_ssl=self.config.USE_SSL,
                tls=self.tls,
                get_info=ALL
            )
            logger.info(f"LDAPS server configured: {self.config.SERVER_HOST}:{self.config.SERVER_PORT}")
        except Exception as e:
            logger.error(f"Server configuration error: {str(e)}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user against LDAPS server
        
        Args:
            username: The Intertech username
            password: The user's password
            
        Returns:
            Dictionary with user information if authentication successful, None otherwise
        """
        if not username or not password:
            logger.warning("Authentication attempted with empty credentials")
            return None
        
        try:
            # Construct the user DN for bind operation
            user_dn = self.config.BIND_DN_TEMPLATE.format(username=username)
            
            # Attempt to bind with user credentials
            conn = Connection(
                self.server,
                user=user_dn,
                password=password,
                auto_bind=True
            )
            
            if conn.bind():
                # Retrieve user attributes
                user_info = self._get_user_info(conn, username)
                conn.unbind()
                logger.info(f"User {username} authenticated successfully via LDAPS")
                return user_info
            else:
                logger.warning(f"LDAPS authentication failed for user {username}: bind unsuccessful")
                return None
                
        except LDAPBindError as e:
            logger.warning(f"LDAPS bind error for {username}: {str(e)}")
            return None
        except LDAPException as e:
            logger.error(f"LDAP error for {username}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected authentication error for {username}: {str(e)}")
            return None
    
    def _get_user_info(self, conn: Connection, username: str) -> Dict[str, Any]:
        """Retrieve user information from LDAP directory"""
        try:
            search_filter = self.config.USER_SEARCH_FILTER.format(username=username)
            conn.search(
                search_base=self.config.USER_SEARCH_BASE,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['uid', 'mail', 'givenName', 'sn', 'cn', 'displayName']
            )
            
            if conn.entries:
                entry = conn.entries[0]
                return {
                    'username': username,
                    'email': str(entry.mail) if hasattr(entry, 'mail') else None,
                    'first_name': str(entry.givenName) if hasattr(entry, 'givenName') else None,
                    'last_name': str(entry.sn) if hasattr(entry, 'sn') else None,
                    'full_name': str(entry.cn) if hasattr(entry, 'cn') else username,
                    'display_name': str(entry.displayName) if hasattr(entry, 'displayName') else username,
                }
            return {'username': username, 'full_name': username}
        except Exception as e:
            logger.error(f"Error retrieving user info: {str(e)}")
            return {'username': username, 'full_name': username}


# Global LDAPS handler instance
ldaps_handler = LDAPSHandler()
