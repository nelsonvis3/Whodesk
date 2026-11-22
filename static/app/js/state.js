export const state = { user: null };
export const isStaff = () => state.user && (state.user.role === "agent" || state.user.role === "admin");
export const isAdmin = () => state.user && state.user.role === "admin";
