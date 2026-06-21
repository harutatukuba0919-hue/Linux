from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
from pathlib import Path

app = Flask(__name__)

# ダウンロード先ディレクトリ
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "yt-dlp")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# サポートされるフォーマット
SUPPORTED_FORMATS = {
    'mp4': 'video/mp4',
    'webm': 'video/webm',
    'mkv': 'video/x-matroska',
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'm4a': 'audio/mp4',
    'flac': 'audio/flac',
}


def get_available_formats(url):
    """URLから利用可能なフォーマットを取得"""
    try:
        ydl_opts = {
            'quiet': False,
            'no_warnings': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 利用可能なフォーマットを収集
            available_formats = set()
            
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('ext'):
                        ext = fmt['ext'].lower()
                        if ext in SUPPORTED_FORMATS:
                            available_formats.add(ext)
            
            # デフォルトの拡張子を追加
            if 'ext' in info:
                ext = info['ext'].lower()
                if ext in SUPPORTED_FORMATS:
                    available_formats.add(ext)
            
            # デフォルト形式
            if not available_formats:
                available_formats.add('mp4')
            
            return {
                'title': info.get('title', 'Unknown'),
                'formats': sorted(list(available_formats)),
            }
    except Exception as e:
        raise Exception(f"フォーマット取得エラー: {str(e)}")


def download_video(url, format_type):
    """動画をダウンロード"""
    try:
        # フォーマット設定
        if format_type in ['mp3', 'wav', 'm4a', 'flac']:
            # オーディオフォーマット
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format_type,
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
            }
        else:
            # ビデオフォーマット
            ydl_opts = {
                'format': 'best[ext=' + format_type + ']/best',
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return {
                'success': True,
                'filename': os.path.basename(filename),
                'title': info.get('title', 'Unknown'),
            }
    except Exception as e:
        raise Exception(f"ダウンロードエラー: {str(e)}")


@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')


@app.route('/api/get-formats', methods=['POST'])
def get_formats():
    """利用可能なフォーマットを取得"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URLが入力されていません'}), 400
        
        result = get_available_formats(url)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/download', methods=['POST'])
def download():
    """動画をダウンロード"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        format_type = data.get('format', 'mp4').strip()
        
        if not url:
            return jsonify({'error': 'URLが入力されていません'}), 400
        
        if format_type not in SUPPORTED_FORMATS:
            return jsonify({'error': '無効なフォーマットです'}), 400
        
        result = download_video(url, format_type)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
