# import os
# import pandas as pd
# import plotly.express as px
# from django.core.files.storage import FileSystemStorage
# from django.shortcuts import render
# from django.http import JsonResponse
# from django.conf import settings

# def index(request):
#     return render(request, 'dashboard/index.html')

# def upload_file(request):
#     if request.method == 'POST' and request.FILES.get('file'):
#         file = request.FILES['file']

#         # ✅ Check if file is CSV
#         if not file.name.endswith('.csv'):
#             return render(request, 'dashboard/upload.html', {'error': 'Only CSV files are allowed.'})

#         # ✅ Save file to MEDIA_ROOT
#         fs = FileSystemStorage(location=settings.MEDIA_ROOT)
#         filename = fs.save(file.name, file)
#         file_path = os.path.join(settings.MEDIA_ROOT, filename)  # ✅ Ensure full file path

#         # ✅ Store file path in session
#         request.session['file_path'] = file_path

#         # ✅ Read file into a DataFrame
#         try:
#             df = pd.read_csv(file_path)
#             preview_df = df.iloc[:5, :5]  # First 5 rows & 5 columns
#         except Exception as e:
#             return render(request, 'dashboard/upload.html', {'error': f'Error processing the file: {e}'})

#         # ✅ Convert preview dataframe to JSON-friendly format
#         preview_data = preview_df.to_dict(orient='records')

#         return render(request, 'dashboard/upload.html', {
#             'file_path': file_path,
#             'preview_data': preview_data
#         })

#     return render(request, 'dashboard/upload.html')

# def dashboard(request):
#     # ✅ Get file path from session
#     file_path = request.session.get('file_path')

#     if not file_path or not os.path.exists(file_path):
#         return render(request, 'dashboard/dashboard.html', {'error': 'No file uploaded yet!'})

#     # ✅ Load dataset safely
#     try:
#         df = pd.read_csv(file_path)

#         # ✅ Step 1: Remove leading/trailing spaces in column names
#         df.columns = df.columns.str.strip()

#         # ✅ Step 2: Convert column names to lowercase for consistency
#         df.columns = df.columns.str.lower()

#         print("Columns found:", df.columns)  # ✅ Debugging

#         # ✅ Step 3: Check if 'year' column exists
#         if 'year' not in df.columns:
#             return render(request, 'dashboard/dashboard.html', {'error': "Column 'Year' not found in dataset!"})

#     except Exception as e:
#         return render(request, 'dashboard/dashboard.html', {'error': f'Error reading the dataset: {e}'})

#     # ✅ Generate summary statistics
#     numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
#     summary_stats = df[numeric_columns].describe().T.to_dict()

#     # ✅ Pass data to template
#     return render(request, 'dashboard/dashboard.html', {
#         'numeric_columns': numeric_columns,
#         'summary_stats': summary_stats,
#         'df_columns': df.columns.tolist()  # ✅ Debugging: See all column names in the template
#     })



# def filtered_data(request):
#     filter_value = request.GET.get('filter', 'all')
#     file_path = request.session.get('file_path')

#     if not file_path or not os.path.exists(file_path):
#         return JsonResponse({'error': 'No file uploaded yet.'})

#     try:
#         df = pd.read_csv(file_path)

#         # ✅ Ensure filtering column exists
#         if filter_value != 'all' and 'Category' in df.columns:
#             df = df[df['Category'] == filter_value]

#         filtered_data = df.to_dict(orient='records')

#         return JsonResponse({'data': filtered_data})

#     except Exception as e:
#         return JsonResponse({'error': f'Error processing the filter: {e}'})


import pandas as pd
import plotly.express as px
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

def index(request):
    return render(request, 'dashboard/index.html')

def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']

        # Check if file is CSV
        if not file.name.endswith('.csv'):
            return render(request, 'dashboard/upload.html', {'error': 'Only CSV files are allowed.'})

        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(file.name, file)
        file_path = fs.url(filename)

        # Read file into a DataFrame
        try:
            df = pd.read_csv(fs.path(filename))
            # Get the first 5 rows and 5 columns
            preview_df = df.iloc[:5, :5]
        except Exception as e:
            return render(request, 'dashboard/upload.html', {'error': 'Error processing the file'})

        # Convert preview dataframe to a dictionary for rendering
        preview_data = preview_df.to_dict(orient='records')

        # Store file path in session for later use in dashboard
        request.session['file_path'] = fs.path(filename)

        return render(request, 'dashboard/upload.html', {'file_path': file_path, 'preview_data': preview_data})

    return render(request, 'dashboard/upload.html')

def dashboard(request):
    # Get the file path from session
    file_path = request.session.get('file_path')

    if not file_path:
        return render(request, 'dashboard/dashboard.html', {'error': 'No file uploaded yet!'})

    # Read the dataset
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return render(request, 'dashboard/dashboard.html', {'error': f'Error reading the dataset: {e}'})

    # Define selected columns
    selected_columns = ["Engine_Size", "Horsepower", "Torque", "Weight", "Top_Speed", "Acceleration_0_100"]

    # Filter only existing columns (avoid errors if some columns are missing)
    existing_columns = [col for col in selected_columns if col in df.columns]

    # Generate summary statistics for selected columns
    if existing_columns:
        summary_stats = df[existing_columns].describe().T  # Transpose for readability
        summary_stats.index.name = "Feature"
        summary_stats_dict = summary_stats.to_dict()  # ✅ Convert DataFrame to dictionary
        summary_stats_html = summary_stats.to_html(classes="table table-bordered", index=True)
    else:
        summary_stats_dict = {}
        summary_stats_html = "<p>No matching numeric columns found in the dataset.</p>"

    # Generate charts (if numeric columns exist)
    bar_graph = pie_graph = hist_graph = scatter_graph = None
    try:
        if len(df.columns) > 1:
            bar_fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=f"Bar Chart of {df.columns[0]} vs {df.columns[1]}")
            bar_graph = bar_fig.to_html(full_html=False)

            pie_fig = px.pie(df, names=df.columns[0], title=f"Pie Chart of {df.columns[0]}")
            pie_graph = pie_fig.to_html(full_html=False)

            hist_fig = px.histogram(df, x=df.columns[1], title=f"Histogram of {df.columns[1]}")
            hist_graph = hist_fig.to_html(full_html=False)

            scatter_fig = px.scatter(df, x=df.columns[0], y=df.columns[1], title=f"Scatter Plot of {df.columns[0]} vs {df.columns[1]}")
            scatter_graph = scatter_fig.to_html(full_html=False)
    except Exception as e:
        print(f"Error generating charts: {e}")

    # Pass everything to the template
    return render(request, 'dashboard/dashboard.html', {
        'df': df.head().to_html(classes="table table-bordered"),  # ✅ Pass DataFrame as HTML table
        'summary_stats_dict': summary_stats_dict,  # ✅ Now it's defined
        'summary_stats_html': summary_stats_html,  # ✅ Table format summary
        'bar_graph': bar_graph,
        'pie_graph': pie_graph,
        'hist_graph': hist_graph,
        'scatter_graph': scatter_graph
    })

def filtered_data(request):
    filter_value = request.GET.get('filter', 'all')
    file_path = request.session.get('file_path')

    if file_path:
        try:
            df = pd.read_csv(file_path)

            if filter_value != 'all' and 'Category' in df.columns:
                df = df[df['Category'] == filter_value]  # Adjust column name as needed

            filtered_data = df.to_dict(orient='records')

            return JsonResponse({'data': filtered_data})

        except Exception as e:
            return JsonResponse({'error': 'Error processing the filter.'})

    return JsonResponse({'error': 'No file uploaded yet.'})
