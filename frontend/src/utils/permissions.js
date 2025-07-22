// 权限常量定义（与后端保持一致）
export const PERMISSIONS = {
  DATA_VIEW: 'data_view',
  DATA_EXPORT: 'data_export',
  DATA_CREATE: 'data_create',
  DATA_UPDATE: 'data_update',
  DATA_DELETE: 'data_delete',
  DATA_IMPORT: 'data_import',
  USER_MANAGE: 'user_manage',
  GROUP_MANAGE: 'group_manage',
  ROLE_MANAGE: 'role_manage',
  AI_SEARCH: 'ai_search',
};

// 权限检查工具类
export class PermissionChecker {
  constructor(user) {
    this.user = user;
  }

  // 检查是否有特定权限
  hasPermission(permission) {
    if (!this.user || !this.user.effective_permissions) {
      return false;
    }
    return this.user.effective_permissions.includes(permission);
  }

  // 检查是否有多个权限中的任意一个
  hasAnyPermission(permissions) {
    return permissions.some(permission => this.hasPermission(permission));
  }

  // 检查是否有所有指定权限
  hasAllPermissions(permissions) {
    return permissions.every(permission => this.hasPermission(permission));
  }

  // 检查是否为管理员
  isAdmin() {
    return this.user?.is_admin || this.user?.role_id === 'admin';
  }

  // 检查是否可以访问特定路由
  canAccessRoute(routePermissions) {
    if (!routePermissions || routePermissions.length === 0) {
      return true; // 无权限要求的路由，所有人都可以访问
    }
    return this.hasAnyPermission(routePermissions);
  }
}

// 路由权限配置
export const ROUTE_PERMISSIONS = {
  '/home': [], // 所有登录用户都可以访问
  '/data-query': [PERMISSIONS.DATA_VIEW],
  '/import': [PERMISSIONS.DATA_IMPORT],
  '/user-management': [PERMISSIONS.USER_MANAGE],
  '/role-management': [PERMISSIONS.ROLE_MANAGE],
  '/group-management': [PERMISSIONS.GROUP_MANAGE],
};

// 菜单项权限配置
export const MENU_PERMISSIONS = {
  home: [],
  'data-query': [PERMISSIONS.DATA_VIEW],
  import: [PERMISSIONS.DATA_IMPORT],
  'user-management': [PERMISSIONS.USER_MANAGE],
  'role-management': [PERMISSIONS.ROLE_MANAGE],
  'group-management': [PERMISSIONS.GROUP_MANAGE],
};

// 创建权限检查器实例的工具函数
export const createPermissionChecker = (user) => {
  return new PermissionChecker(user);
};

// React Hook：权限检查
export const usePermissions = (user) => {
  const checker = new PermissionChecker(user);
  
  return {
    hasPermission: (permission) => checker.hasPermission(permission),
    hasAnyPermission: (permissions) => checker.hasAnyPermission(permissions),
    hasAllPermissions: (permissions) => checker.hasAllPermissions(permissions),
    isAdmin: () => checker.isAdmin(),
    canAccessRoute: (routePermissions) => checker.canAccessRoute(routePermissions),
    checker
  };
};