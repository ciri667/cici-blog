export interface Post {
  id: number;
  title: string;
  slug: string;
  content: string;
  excerpt: string | null;
  cover_image_url: string | null;
  tags: string[] | null;
  category: string | null;
  status: string;
  author_id: number | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PostListItem {
  id: number;
  title: string;
  slug: string;
  excerpt: string | null;
  cover_image_url: string | null;
  tags: string[] | null;
  category: string | null;
  status: string;
  published_at: string | null;
  created_at: string;
}

export interface PostListResponse {
  items: PostListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface NewsArticle {
  id: number;
  title: string;
  slug: string;
  original_url: string;
  original_title: string;
  source_name: string | null;
  summary: string | null;
  ai_commentary: string | null;
  tags: string[] | null;
  category: string | null;
  status: string;
  cover_image_url: string | null;
  published_at: string | null;
  fetched_at: string;
  created_at: string;
}

export interface NewsListItem {
  id: number;
  title: string;
  slug: string;
  source_name: string | null;
  summary: string | null;
  tags: string[] | null;
  category: string | null;
  status: string;
  published_at: string | null;
  created_at: string;
}

export interface NewsListResponse {
  items: NewsListItem[];
  total: number;
  page: number;
  page_size: number;
}
