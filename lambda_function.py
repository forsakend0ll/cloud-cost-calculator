import boto3
import json
import datetime
import traceback

def lambda_handler(event, context):
    # Initialize clients
    ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer
    s3 = boto3.client('s3')
    sns = boto3.client('sns')

    # Replace with your actual resources
    bucket_name = 'cloud-cost-tracker-cloudwithpaula'
    sns_topic_arn = 'arn:aws:sns:us-east-1:019511185150:CostAlerts'

    try:
        # Set date range for the last 7 days
        end = datetime.date.today()
        start = end - datetime.timedelta(days=7)

        # Query AWS Cost Explorer
        response = ce.get_cost_and_usage(
            TimePeriod={'Start': start.strftime('%Y-%m-%d'), 'End': end.strftime('%Y-%m-%d')},
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )

        # Prepare the report data
        report = response['ResultsByTime']
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        filename = f"reports/weekly-report-{date_str}.json"

        # Upload to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=json.dumps(report, indent=2)
        )

        # Send success notification
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject='✅ AWS Cost Report Generated',
            Message=f'Your weekly cost report has been uploaded to S3:\n\ns3://{bucket_name}/{filename}'
        )

        return {
            'statusCode': 200,
            'body': json.dumps(f"Report uploaded to {bucket_name}/{filename}")
        }

    except Exception as e:
        # Send failure notification
        error_message = f"❌ Failed to generate cost report: {str(e)}\n\n{traceback.format_exc()}"
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject='❌ AWS Cost Report Failed',
            Message=error_message
        )

        return {
            'statusCode': 500,
            'body': json.dumps('Error generating report')
        }
