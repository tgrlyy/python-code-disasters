pipeline {
  agent any

  environment {
    SONAR_SCANNER_OPTS = "-Xmx2048m"
  }

  stages {
    stage('SonarQube Analysis + Quality Gate') {
      steps {
        withSonarQubeEnv('sonarqube-server') {
          withCredentials([string(credentialsId: 'd10555ea-7c4b-40f7-9108-652b3aa63528', variable: 'SONAR_AUTH_TOKEN')]) {
            script {
              def scannerHome = tool 'sonar-scanner'
              sh """
                ${scannerHome}/bin/sonar-scanner \
                  -Dsonar.projectKey=python-project \
                  -Dsonar.sources=. \
                  -Dsonar.language=py \
                  -Dsonar.sourceEncoding=UTF-8 \
                  -Dsonar.host.url=$SONAR_HOST_URL \
                  -Dsonar.token=$SONAR_AUTH_TOKEN | tee sonar.log
              """

              env.CE_TASK_ID = sh(
                script: "grep -o 'ce/task?id=[^ ]*' sonar.log | sed 's/.*id=//' | tail -1",
                returnStdout: true
              ).trim()
              echo "SonarQube task ID: ${env.CE_TASK_ID}"

              echo "Polling SonarQube API for Quality Gate result..."
              timeout(time: 3, unit: 'MINUTES') {
                waitUntil {
                  def status = sh(
                    script: """curl -s -u $SONAR_AUTH_TOKEN: $SONAR_HOST_URL/api/ce/task?id=${env.CE_TASK_ID} | grep -o '"status":"[^"]*"' | head -1 | cut -d':' -f2 | tr -d '"' || echo 'NULL'""",
                    returnStdout: true
                  ).trim()
                  echo "Current task status: ${status}"

                  if (status == "SUCCESS") {
                    def qg = sh(
                      script: """curl -s -u $SONAR_AUTH_TOKEN: $SONAR_HOST_URL/api/qualitygates/project_status?projectKey=python-project | grep -o '"status":"[^"]*"' | head -1 | cut -d':' -f2 | tr -d '"'""",
                      returnStdout: true
                    ).trim()
                    echo "Quality Gate status: ${qg}"

                    if (qg != "OK") {
                      error "Quality Gate failed: Skipping Hadoop job."
                    } else {
                      echo "Quality Gate passed!"
                    }
                    return true
                  } else if (status == "FAILED") {
                    error "Sonar analysis failed."
                  } else if (status == "NULL" || status == "") {
                    echo "API request failed or still processing, retrying..."
                    sleep 5
                    return false
                  } else {
                    sleep 5
                    return false
                  }
                }
              }
            }
          }
        }
      }
    }

    stage('Authenticate to Hadoop Project') {
      steps {
        withCredentials([file(credentialsId: '28bc177a-3504-4f54-a8e6-ea3a0c9be25e', variable: 'GOOGLE_CLOUD_KEYFILE_JSON')]) {
            sh '''
                gcloud auth activate-service-account --key-file=$GOOGLE_CLOUD_KEYFILE_JSON
                gcloud container clusters get-credentials hadoop-cluster \
                  --zone=us-west1-a \
                  --project=cloud-infra-project-474322
            '''
        }
      }
    }

    stage('Run Hadoop Job') {
      steps {
        sh '''
          kubectl cp -n hadoop mapper.py hadoop-hadoop-hdfs-nn-0:/tmp/
          kubectl cp -n hadoop reducer.py hadoop-hadoop-hdfs-nn-0:/tmp/
          kubectl exec -n hadoop -it hadoop-hadoop-hdfs-nn-0 -- bash -lc '
            /opt/hadoop/bin/hdfs dfs -rm -r -f /user/jenkins/output || true &&
            /opt/hadoop/bin/hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming*.jar \
              -files /tmp/mapper.py,/tmp/reducer.py \
              -mapper "python3 mapper.py" \
              -reducer "python3 reducer.py" \
              -input /user/jenkins/repo/python-code-disasters \
              -output /user/jenkins/output
          '
          kubectl exec -n hadoop -it hadoop-hadoop-hdfs-nn-0 -- bash -lc '/opt/hadoop/bin/hdfs dfs -cat /user/jenkins/output/part-*'
        '''
      }
    }
  }

  post {
    always {
      echo "View SonarQube results at: ${env.SONAR_HOST_URL}/dashboard?id=python-project"
    }
  }
}