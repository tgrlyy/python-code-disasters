pipeline {
  agent any

  environment {
    SONAR_SCANNER_OPTS = "-Xmx2048m"
  }

  stages {
    stage('SonarQube Analysis') {
      steps {
        withSonarQubeEnv('sonarqube-server') {
          script {
            def scannerHome = tool 'sonar-scanner'
            sh """
              ${scannerHome}/bin/sonar-scanner \
                -Dsonar.projectKey=python-project \
                -Dsonar.sources=. \
                -Dsonar.language=py \
                -Dsonar.sourceEncoding=UTF-8 \
                -Dsonar.host.url=$SONAR_HOST_URL \
                -Dsonar.token=$SONAR_AUTH_TOKEN
            """
          }
        }
      }
    }

    stage('Quality Gate') {
      steps {
        script {
          def qg = waitForQualityGate()
          if (qg.status != 'OK') {
            error "Quality Gate failed: Skipping Hadoop job."
          } else {
            echo "Quality Gate passed!"
          }
        }
      }
    }

    stage('Authenticate to Hadoop Project') {
      steps {
        withCredentials([file(credentialsId: 'hadoop-sa-json', variable: 'GOOGLE_CLOUD_KEYFILE_JSON')]) {
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