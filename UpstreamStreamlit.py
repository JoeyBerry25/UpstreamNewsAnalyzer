import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import time

# Set page config
st.set_page_config(
    page_title="SLB News Relevance Analyzer",
    page_icon="🛢️",
    layout="wide"
)

# Initialize session state for keywords
if 'keywords_initialized' not in st.session_state:
    st.session_state.keywords_initialized = True

    # Default keyword categories
    st.session_state.high_keywords = [
        'slb', 'schlumberger', 'halliburton', 'baker hughes', 'oilfield services',
        'drilling', 'completion', 'fracking', 'hydraulic fracturing', 'well services',
        'subsurface', 'reservoir', 'logging', 'wireline', 'coiled tubing',
        'artificial lift', 'stimulation', 'cementing', 'mud logging',
        'directional drilling', 'mwd', 'lwd', 'measurement while drilling',
        'carbon capture', 'ccs', 'ccus', 'sequestration', 'co2 injection',
        'digital oilfield', 'petrotechnical', 'geophysics', 'petrophysics'
    ]

    st.session_state.moderate_keywords = [
        'exploration', 'production', 'upstream', 'offshore', 'deepwater',
        'unconventional', 'shale', 'tight oil', 'enhanced recovery',
        'field development', 'project sanctioning', 'final investment decision',
        'technology', 'innovation', 'digitalization', 'automation',
        'esg', 'sustainability', 'emissions', 'decarbonization',
        'lng', 'natural gas', 'oil price', 'commodity', 'energy transition'
    ]

    st.session_state.relevant_keywords = [
        'refining', 'downstream', 'petrochemicals', 'marketing',
        'renewable', 'solar', 'wind', 'hydrogen', 'electric vehicle',
        'pipeline', 'midstream', 'transportation', 'storage'
    ]


def fetch_rss_feed(url):
    """Fetch and parse RSS feed"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        st.error(f"Error fetching RSS feed: {e}")
        return None


def parse_rss_content(xml_content):
    """Parse RSS XML content and extract story information"""
    try:
        root = ET.fromstring(xml_content)
        stories = []

        # Find all item elements
        for item in root.findall('.//item'):
            story = {}

            # Extract basic information with null checks
            title_elem = item.find('title')
            story['title'] = title_elem.text.strip() if title_elem is not None and title_elem.text else "No title"

            link_elem = item.find('link')
            story['link'] = link_elem.text.strip() if link_elem is not None and link_elem.text else ""

            description_elem = item.find('description')
            story[
                'description'] = description_elem.text.strip() if description_elem is not None and description_elem.text else ""

            # Extract publication date
            pub_date_elem = item.find('pubDate')
            if pub_date_elem is not None and pub_date_elem.text:
                try:
                    # Parse the date string
                    date_str = pub_date_elem.text
                    # Extract just the date part (assuming format like "Fri, 20 Jun 2025 18:11:59 +0200")
                    date_match = re.search(r'(\d{1,2} \w{3} \d{4})', date_str)
                    if date_match:
                        story['date'] = date_match.group(1)
                    else:
                        story['date'] = date_str[:10] if len(date_str) > 10 else date_str
                except:
                    story['date'] = pub_date_elem.text if pub_date_elem.text else "Unknown"
            else:
                story['date'] = "Unknown"

            # Extract author
            author_elem = item.find('author')
            story['author'] = author_elem.text.strip() if author_elem is not None and author_elem.text else "Unknown"

            # Extract categories
            categories = []
            for category in item.findall('category'):
                if category.text and category.text.strip():
                    categories.append(category.text.strip())
            story['categories'] = ', '.join(categories) if categories else ""

            stories.append(story)

        return stories
    except ET.ParseError as e:
        st.error(f"Error parsing XML: {e}")
        return []


def analyze_slb_relevance(story):
    """Analyze how relevant a story is to SLB employees using current keyword settings"""
    title = (story['title'] or '').lower()
    description = (story['description'] or '').lower()
    categories = (story['categories'] or '').lower()

    # Combined text for analysis
    text = f"{title} {description} {categories}"

    # Get keywords from session state
    high_keywords = [kw.lower() for kw in st.session_state.high_keywords]
    moderate_keywords = [kw.lower() for kw in st.session_state.moderate_keywords]
    relevant_keywords = [kw.lower() for kw in st.session_state.relevant_keywords]

    # Calculate relevance score
    high_count = sum(1 for keyword in high_keywords if keyword in text)
    moderate_count = sum(1 for keyword in moderate_keywords if keyword in text)
    relevant_count = sum(1 for keyword in relevant_keywords if keyword in text)

    # Determine relevance level
    if high_count >= 2 or 'slb' in text or 'schlumberger' in text:
        return 'High'
    elif high_count >= 1 or moderate_count >= 2:
        return 'Moderate'
    elif moderate_count >= 1 or relevant_count >= 1:
        return 'Relevant'
    else:
        return 'Low'


def create_editorial_summary(story):
    """Create editorial summary from RSS description with proper formatting"""
    description = story['description']
    date = story['date']

    # Clean up description if needed
    if len(description) > 300:
        # Find a good breaking point
        sentences = re.split(r'[.!?]+', description)
        summary_parts = []
        char_count = 0

        for sentence in sentences:
            if char_count + len(sentence) > 250:
                break
            summary_parts.append(sentence.strip())
            char_count += len(sentence)

        summary = '. '.join(summary_parts)
        if not summary.endswith(('.', '!', '?')):
            summary += '.'
    else:
        summary = description.strip()
        if not summary.endswith(('.', '!', '?')):
            summary += '.'

    # Format: Summary | Date | Upstream
    formatted_summary = f"{summary} | {date} | Upstream"
    return formatted_summary


def keyword_manager():
    """Create drag-and-drop keyword management interface"""
    st.sidebar.header("🏷️ Keyword Management")
    st.sidebar.markdown("*Drag keywords between categories to change story relevance*")

    # Create tabs for each category
    high_tab, moderate_tab, relevant_tab = st.sidebar.tabs(["High", "Moderate", "Relevant"])

    with high_tab:
        st.markdown("**High Relevance Keywords**")
        st.markdown("*Direct SLB business, core technologies*")

        # Show current high keywords with remove buttons
        for i, keyword in enumerate(st.session_state.high_keywords):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.text(keyword)
            with col2:
                if st.button("↓", key=f"high_to_mod_{i}", help="Move to Moderate"):
                    st.session_state.moderate_keywords.append(keyword)
                    st.session_state.high_keywords.remove(keyword)
                    st.rerun()
            with col3:
                if st.button("→", key=f"high_to_rel_{i}", help="Move to Relevant"):
                    st.session_state.relevant_keywords.append(keyword)
                    st.session_state.high_keywords.remove(keyword)
                    st.rerun()

        # Add new keyword
        new_high = st.text_input("Add new high relevance keyword:", key="new_high")
        if st.button("Add", key="add_high") and new_high:
            if new_high.lower() not in [kw.lower() for kw in st.session_state.high_keywords]:
                st.session_state.high_keywords.append(new_high.lower())
                st.rerun()

    with moderate_tab:
        st.markdown("**Moderate Relevance Keywords**")
        st.markdown("*Upstream activities, industry trends*")

        for i, keyword in enumerate(st.session_state.moderate_keywords):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.text(keyword)
            with col2:
                if st.button("↑", key=f"mod_to_high_{i}", help="Move to High"):
                    st.session_state.high_keywords.append(keyword)
                    st.session_state.moderate_keywords.remove(keyword)
                    st.rerun()
            with col3:
                if st.button("→", key=f"mod_to_rel_{i}", help="Move to Relevant"):
                    st.session_state.relevant_keywords.append(keyword)
                    st.session_state.moderate_keywords.remove(keyword)
                    st.rerun()

        new_moderate = st.text_input("Add new moderate relevance keyword:", key="new_moderate")
        if st.button("Add", key="add_moderate") and new_moderate:
            if new_moderate.lower() not in [kw.lower() for kw in st.session_state.moderate_keywords]:
                st.session_state.moderate_keywords.append(new_moderate.lower())
                st.rerun()

    with relevant_tab:
        st.markdown("**Relevant Keywords**")
        st.markdown("*General energy industry*")

        for i, keyword in enumerate(st.session_state.relevant_keywords):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.text(keyword)
            with col2:
                if st.button("↑", key=f"rel_to_high_{i}", help="Move to High"):
                    st.session_state.high_keywords.append(keyword)
                    st.session_state.relevant_keywords.remove(keyword)
                    st.rerun()
            with col3:
                if st.button("↓", key=f"rel_to_mod_{i}", help="Move to Moderate"):
                    st.session_state.moderate_keywords.append(keyword)
                    st.session_state.relevant_keywords.remove(keyword)
                    st.rerun()

        new_relevant = st.text_input("Add new relevant keyword:", key="new_relevant")
        if st.button("Add", key="add_relevant") and new_relevant:
            if new_relevant.lower() not in [kw.lower() for kw in st.session_state.relevant_keywords]:
                st.session_state.relevant_keywords.append(new_relevant.lower())
                st.rerun()

    # Reset to defaults button
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Reset to Default Keywords"):
        st.session_state.keywords_initialized = False
        st.rerun()

    # Show keyword counts
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Current Keyword Counts:**")
    st.sidebar.write(f"High: {len(st.session_state.high_keywords)}")
    st.sidebar.write(f"Moderate: {len(st.session_state.moderate_keywords)}")
    st.sidebar.write(f"Relevant: {len(st.session_state.relevant_keywords)}")


def main():
    st.title("🛢️ SLB News Relevance Analyzer")
    st.markdown("*Analyzing Upstream Online RSS feed for stories relevant to SLB employees*")

    # Keyword management in sidebar
    keyword_manager()

    # Configuration options
    st.sidebar.header("⚙️ Configuration")

    # Processing options
    max_stories = st.sidebar.slider("Max stories to analyze", 10, 200, 200,
                                    help="Number of stories to process from RSS feed")

    # RSS feed URL
    rss_url = "https://services.upstreamonline.com/api/feed/rss"

    # Add refresh button
    if st.button("🔄 Refresh Feed", type="primary"):
        st.cache_data.clear()

    # Fetch and process the feed
    with st.spinner("Fetching and analyzing RSS feed..."):
        xml_content = fetch_rss_feed(rss_url)

        if xml_content:
            stories = parse_rss_content(xml_content)

            if stories:
                # Limit to max_stories
                stories = stories[:max_stories]

                # Analyze relevance and create summaries
                processed_stories = []
                progress_bar = st.progress(0)

                for i, story in enumerate(stories):
                    progress_bar.progress((i + 1) / len(stories))

                    # Analyze relevance using current keywords
                    relevance = analyze_slb_relevance(story)

                    # Create editorial summary from RSS description
                    editorial_summary = create_editorial_summary(story)

                    processed_stories.append({
                        'Title': story['title'],
                        'Relevance': relevance,
                        'Editorial Summary': editorial_summary,
                        'Date': story['date'],
                        'Author': story['author'],
                        'Categories': story['categories'],
                        'Link': story['link']
                    })

                progress_bar.empty()

                # Create DataFrame
                df = pd.DataFrame(processed_stories)

                # Sort by relevance (High -> Moderate -> Relevant -> Low)
                relevance_order = {'High': 0, 'Moderate': 1, 'Relevant': 2, 'Low': 3}
                df['sort_order'] = df['Relevance'].map(relevance_order)
                df = df.sort_values('sort_order').drop('sort_order', axis=1)

                # Display summary stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Stories", len(df))
                with col2:
                    st.metric("High Relevance", len(df[df['Relevance'] == 'High']))
                with col3:
                    st.metric("Moderate Relevance", len(df[df['Relevance'] == 'Moderate']))
                with col4:
                    st.metric("Relevant", len(df[df['Relevance'] == 'Relevant']))

                # Filter options
                st.sidebar.header("🔍 Filters")
                relevance_filter = st.sidebar.multiselect(
                    "Select Relevance Levels",
                    options=['High', 'Moderate', 'Relevant', 'Low'],
                    default=['High', 'Moderate', 'Relevant', 'Low']
                )

                # Apply filters
                if relevance_filter:
                    filtered_df = df[df['Relevance'].isin(relevance_filter)]
                else:
                    filtered_df = df

                # Display the table
                st.header(f"📊 News Stories ({len(filtered_df)} stories)")

                # Apply styling based on relevance
                def color_relevance(val):
                    if val == 'High':
                        return 'background-color: #ffebee; color: #c62828'
                    elif val == 'Moderate':
                        return 'background-color: #fff3e0; color: #ef6c00'
                    elif val == 'Relevant':
                        return 'background-color: #f3e5f5; color: #7b1fa2'
                    else:
                        return 'background-color: #f5f5f5; color: #616161'

                # Display table with clickable links
                if not filtered_df.empty:
                    # Create display dataframe
                    display_df = filtered_df.copy()

                    # Create clickable links
                    def make_clickable_safe(link):
                        if link and link.startswith('http'):
                            return f'<a href="{link}" target="_blank">🔗 Read Story</a>'
                        else:
                            return "No link available"

                    display_df['Link'] = display_df['Link'].apply(make_clickable_safe)

                    # Style the dataframe
                    styled_df = display_df.style.map(
                        color_relevance, subset=['Relevance']
                    ).set_properties(**{
                        'text-align': 'left',
                        'white-space': 'pre-wrap'
                    })

                    # Display as HTML to enable clickable links
                    st.write(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

                    # Download option
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"slb_news_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No stories match the selected filters.")
            else:
                st.error("No stories found in the RSS feed.")
        else:
            st.error("Failed to fetch RSS feed.")

    # Add information about the analysis
    with st.expander("ℹ️ About This Analysis"):
        st.markdown(f"""
        **Relevance Criteria:**

        - **High**: Direct mentions of SLB/Schlumberger, major oilfield services news, core technology areas
        - **Moderate**: Upstream technology, field development, exploration activities, energy transition topics  
        - **Relevant**: General oil & gas industry news, market conditions, regulatory changes
        - **Low**: Topics with minimal relevance to SLB's business

        **Keyword Management:**

        Use the sidebar to customize which keywords determine story relevance:
        - **Add new keywords** to any category
        - **Move keywords** between categories using arrow buttons
        - **Reset to defaults** if needed
        - Stories are **automatically re-ranked** when keywords change

        **Editorial Summary Format:**

        Each story summary follows the format: `[Content] | [Date] | Upstream`
        - Uses RSS feed descriptions for reliable content
        - Includes publication date and source attribution
        - Formatted for professional news consumption

        **Data Source:** Upstream Online RSS Feed

        **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)


if __name__ == "__main__":
    main()