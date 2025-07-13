import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

# Konfigurasi halaman
st.set_page_config(
    page_title="Book Search App",
    page_icon="📚",
    layout="wide"
)

# Fungsi untuk memuat data
@st.cache_data
def load_data():
    try:
        with open('data/books.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except FileNotFoundError:
        st.error("File data/books.json tidak ditemukan. Pastikan Anda telah menjalankan spider terlebih dahulu.")
        return pd.DataFrame()

# Fungsi untuk membersihkan harga
def clean_price(price):
    if price:
        return float(re.sub(r'[£,]', '', price))
    return 0

# Fungsi untuk filter data
def filter_data(df, search_term, category, min_rating, max_price):
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['title'].str.contains(search_term, case=False, na=False) |
            filtered_df['description'].str.contains(search_term, case=False, na=False)
        ]
    
    if category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == category]
    
    if min_rating > 0:
        filtered_df = filtered_df[filtered_df['rating'] >= min_rating]
    
    if max_price > 0:
        filtered_df = filtered_df[filtered_df['price_numeric'] <= max_price]
    
    return filtered_df

# Header aplikasi
st.title("📚 Book Search App")
st.subheader("Pencarian dan Analisis Buku dari Books to Scrape")

# Load data
df = load_data()

if not df.empty:
    # Preprocessing data
    df['price_numeric'] = df['price'].apply(clean_price)
    df['rating'] = df['rating'].fillna(0)
    df['category'] = df['category'].fillna('Unknown')
    
    # Sidebar untuk filter
    st.sidebar.header("🔍 Filter Pencarian")
    
    search_term = st.sidebar.text_input("Cari berdasarkan judul atau deskripsi:")
    
    categories = ['All'] + sorted(df['category'].unique().tolist())
    selected_category = st.sidebar.selectbox("Pilih kategori:", categories)
    
    min_rating = st.sidebar.slider("Rating minimum:", 0, 5, 0)
    
    max_price = st.sidebar.slider("Harga maksimum (£):", 0, int(df['price_numeric'].max()), int(df['price_numeric'].max()))
    
    # Filter data
    filtered_df = filter_data(df, search_term, selected_category, min_rating, max_price)
    
    # Statistik umum
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Buku", len(df))
    
    with col2:
        st.metric("Buku Ditemukan", len(filtered_df))
    
    with col3:
        st.metric("Rata-rata Rating", f"{df['rating'].mean():.1f}")
    
    with col4:
        st.metric("Rata-rata Harga", f"£{df['price_numeric'].mean():.2f}")
    
    # Tabs untuk berbagai view
    tab1, tab2, tab3 = st.tabs(["📋 Daftar Buku", "📊 Visualisasi", "📈 Analisis"])
    
    with tab1:
        st.subheader("Daftar Buku")
        
        if not filtered_df.empty:
            # Tampilkan hasil pencarian
            for idx, book in filtered_df.iterrows():
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if book['image_url']:
                        st.image(book['image_url'], width=120)
                    else:
                        st.write("📖")
                
                with col2:
                    st.write(f"**{book['title']}**")
                    st.write(f"💰 Harga: {book['price']}")
                    st.write(f"⭐ Rating: {'⭐' * int(book['rating'])}")
                    st.write(f"📂 Kategori: {book['category']}")
                    st.write(f"📦 Ketersediaan: {book['availability']}")
                    if book['description']:
                        st.write(f"📝 Deskripsi: {book['description'][:200]}...")
                    st.write(f"🔢 UPC: {book['upc']}")
                    st.write("---")
        else:
            st.write("Tidak ada buku yang sesuai dengan kriteria pencarian.")
    
    with tab2:
        st.subheader("Visualisasi Data")
        
        # Distribusi rating
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Distribusi Rating Buku**")
            rating_counts = df['rating'].value_counts().sort_index()
            fig_rating = px.bar(
                x=rating_counts.index,
                y=rating_counts.values,
                labels={'x': 'Rating', 'y': 'Jumlah Buku'},
                title="Distribusi Rating"
            )
            st.plotly_chart(fig_rating, use_container_width=True)
        
        with col2:
            st.write("**Top 10 Kategori Buku**")
            category_counts = df['category'].value_counts().head(10)
            fig_category = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Top 10 Kategori"
            )
            st.plotly_chart(fig_category, use_container_width=True)
        
        # Distribusi harga
        st.write("**Distribusi Harga Buku**")
        fig_price = px.histogram(
            df,
            x='price_numeric',
            nbins=30,
            title="Distribusi Harga Buku",
            labels={'price_numeric': 'Harga (£)', 'count': 'Jumlah Buku'}
        )
        st.plotly_chart(fig_price, use_container_width=True)
    
    with tab3:
        st.subheader("Analisis Data")
        
        # Statistik kategori
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Statistik per Kategori**")
            category_stats = df.groupby('category').agg({
                'price_numeric': ['mean', 'count'],
                'rating': 'mean'
            }).round(2)
            category_stats.columns = ['Rata-rata Harga', 'Jumlah Buku', 'Rata-rata Rating']
            category_stats = category_stats.sort_values('Jumlah Buku', ascending=False)
            st.dataframe(category_stats.head(10))
        
        with col2:
            st.write("**Buku Termahal**")
            top_expensive = df.nlargest(10, 'price_numeric')[['title', 'price', 'rating', 'category']]
            st.dataframe(top_expensive.reset_index(drop=True))
        
        # Korelasi rating dan harga
        st.write("**Korelasi Rating vs Harga**")
        fig_scatter = px.scatter(
            df,
            x='rating',
            y='price_numeric',
            color='category',
            title="Korelasi Rating vs Harga",
            labels={'rating': 'Rating', 'price_numeric': 'Harga (£)'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Insight
        st.write("**Insight Data:**")
        st.write(f"• Total buku yang berhasil di-scrape: {len(df)}")
        st.write(f"• Kategori terbanyak: {df['category'].value_counts().index[0]} ({df['category'].value_counts().iloc[0]} buku)")
        st.write(f"• Buku termahal: {df.loc[df['price_numeric'].idxmax(), 'title']} (£{df['price_numeric'].max():.2f})")
        st.write(f"• Buku termurah: {df.loc[df['price_numeric'].idxmin(), 'title']} (£{df['price_numeric'].min():.2f})")
        st.write(f"• Rating tertinggi: {df['rating'].max()}/5")
        st.write(f"• Jumlah buku dengan rating 5: {len(df[df['rating'] == 5])}")

else:
    st.warning("Data tidak tersedia. Silakan jalankan spider terlebih dahulu untuk mengumpulkan data.")
    st.code("scrapy crawl books -o data/books.json")

# Footer
st.markdown("---")
st.markdown("**Dibuat untuk UAS Information Retrieval - Universitas Abulyatama 2025**")