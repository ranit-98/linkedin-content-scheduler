export const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
export const endpoints = {
  auth: { linkedin: { authorize: '/api/v1/auth/linkedin/authorize' } },
  connections: { list: '/api/v1/connections', mock: '/api/v1/connections/mock' },
  posts: {
    list: '/api/v1/posts',
    create: '/api/v1/posts',
    image: (postId: string) => `/api/v1/posts/${postId}/image`,
  },
};
export const getLinkedInAuthorizeUrl = () =>
  new URL(endpoints.auth.linkedin.authorize, apiBaseUrl).toString();
export const getPostImageUrl = (postId: string) =>
  new URL(endpoints.posts.image(postId), apiBaseUrl).toString();
