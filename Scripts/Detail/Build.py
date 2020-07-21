#!/bin/echo "This module must be imported by other Python scripts."

import os, platform, re, shutil, glob

from Detail.Config import config
import Detail.Utility as utility

class BuildSystem:

   platformString = ""

   productVersion = "x.y.z"
   productStage = "stage"
   productBaseName = "Synergy"
   productPackageName = ""

   def __configureSubmodules( self ):

      utility.printHeading( "Updating Git submodules..." )

      utility.runCommand(
         'pushd "' + config.toplevelPath() + '" && '
         "git submodule update --init --remote --recursive && "
         "popd" )

   def __configureCMake( self ):

      utility.printHeading( "Configuring CMake..." )

      command = ( "cmake"
         ' -S "' + config.synergyCorePath() + '" '
         ' -B "' + config.synergyBuildPath() + '" '
         " -D CMAKE_BUILD_TYPE=Release "
         " -D CMAKE_CONFIGURATION_TYPES=Release "
         " -D SYNERGY_ENTERPRISE=ON " )

      if platform.system() == "Darwin":
         command += " -D CMAKE_OSX_DEPLOYMENT_TARGET=10.12 "
         command += " -D CMAKE_OSX_ARCHITECTURES=x86_64 "

      if config.libQtPath() != "":
         command += ' -D CMAKE_PREFIX_PATH="' + config.libQtPath() +'" '

      if config.cmakeGenerator() != "":
         command += ' -G "' + config.cmakeGenerator() + '" '

      if config.vcvarsallPath() != "":
         command = 'call "' + config.vcvarsallPath() + '" x64 && ' + command

      utility.runCommand( command )

   def __configureVersion( self ):

      utility.printHeading( "Configuring version information..." )

      self.platformString = "-".join( [ platform.system(), platform.release(), platform.machine() ] )

      versionFile = open( config.synergyVersionPath(), "r" )
      versionData = versionFile.read();
      versionFile.close()

      matches = re.findall( r"(?: +SET +)?SYNERGY_VERSION_\w+ *= *(\w+)", versionData )

      if len( matches ) != 4:
         printError( "Failed to extract version information." )
         raise SystemExit( 1 )

      self.productVersion = ".".join( [ matches[ 0 ], matches[ 1 ], matches[ 2 ] ] )
      self.productStage = matches[ 3 ]

      self.productPackageName = "-".join( [ self.productBaseName, self.productVersion, self.productStage, self.platformString ] ).lower()

      utility.printItem( "platformString: ", self.platformString )
      utility.printItem( "productVersion: ", self.productVersion )
      utility.printItem( "productStage: ", self.productStage )
      utility.printItem( "productPackageName: ", self.productPackageName )

   def configure( self ):

      self.__configureSubmodules()
      self.__configureCMake()
      self.__configureVersion()

   # Windows builds
   def __windowsMakeBinaries( self ):

      utility.printHeading( "Building binaries..." )

      utility.runCommand(
         'pushd "' + config.synergyBuildPath() + '" && '
         'call "' + config.vcvarsallPath() + '" x64 && '
         'msbuild synergy-core.sln /p:Platform="x64" /p:Configuration=Release /m && '
         "popd" )

   def __windowsMakeMSI( self ):

      utility.printHeading( "Building MSI package..." )

      installerPath = utility.joinPath( config.synergyBuildPath(), "installer" )

      utility.runCommand(
         'pushd "' + installerPath + '" && '
         'call "' + config.vcvarsallPath() + '" x64 && '
         'msbuild Synergy.sln /p:Configuration=Release && '
         "popd" )

      sourcePath = utility.joinPath( installerPath, "bin/Release/Synergy.msi" )
      targetPath = utility.joinPath( config.binariesPath(), self.productPackageName + ".msi" )

      shutil.move( sourcePath, targetPath )

   def __windowsMakeZIP( self ):

      utility.printHeading( "Building standalone ZIP package..." )

      def copySynergyBinaries( sourcePath, productPath ):

         fileList = [
            "libEGL.dll",
            "libGLESv2.dll",
            "Qt5Core.dll",
            "Qt5Gui.dll",
            "Qt5Network.dll",
            "Qt5Svg.dll",
            "Qt5Widgets.dll",
            "synergy.exe",
            "synergyc.exe",
            "synergyd.exe",
            "synergys.exe",
            "syntool.exe"
            ]

         if not os.path.exists( productPath ):
            os.mkdir( productPath )

         for fileName in fileList:
            filePath = utility.joinPath( sourcePath, fileName )
            shutil.copy2( filePath, productPath )

         shutil.copytree( utility.joinPath( sourcePath, "Platforms" ), utility.joinPath( productPath, "Platforms" ), dirs_exist_ok = True )
         shutil.copytree( utility.joinPath( sourcePath, "Styles"    ), utility.joinPath( productPath, "Styles"    ), dirs_exist_ok = True )

      def copyOpenSSLBinaries( sourceOpenSSLPath, productPath ):

         productOpenSSLPath = utility.joinPath( productPath, "OpenSSL" )

         if not os.path.exists( productOpenSSLPath ):
            os.mkdir( productOpenSSLPath )

         for filePath in glob.glob( sourceOpenSSLPath + "/*" ):
            shutil.copy2( filePath, productOpenSSLPath )

         for filePath in glob.glob( sourceOpenSSLPath + "/*.dll" ):
            shutil.copy2( filePath, productPath )

      def makeZipArchive( productPath, zipPath ):

         rootPath = utility.joinPath( productPath, ".." )
         basePath = os.path.relpath( productPath, rootPath )

         shutil.make_archive( zipPath, 'zip', rootPath, basePath )

      sourcePath = utility.joinPath( config.synergyBuildPath(), "bin/Release" )
      productPath = utility.joinPath( config.synergyBuildPath(), "bin", self.productPackageName )

      copySynergyBinaries( sourcePath, productPath )

      sourceOpenSSLPath = utility.joinPath( config.synergyCorePath(), "ext/openssl/windows/x64/bin" )

      copyOpenSSLBinaries( sourceOpenSSLPath, productPath )

      zipPath = utility.joinPath( config.binariesPath(), self.productPackageName )

      makeZipArchive( productPath, zipPath )

   # Darwin builds
   def __darwinMakeApplication( self ):

      utility.printHeading( "Building application bundle..." )

   def __darwinMakeDMG( self ):

      utility.printHeading( "Building DMG disk image file..." )

   # Linux builds
   def __linuxMakeBinaries( self ):

      utility.printHeading( "Building binaries..." )

   def __linuxMakeAppImage( self ):

      utility.printHeading( "Building AppImage package..." )

   def __linuxMakeDeb( self ):

      utility.printHeading( "Building Debian package..." )

   def make( self ):

      if platform.system() == "Windows":
         self.__windowsMakeBinaries()
         self.__windowsMakeMSI()
         self.__windowsMakeZIP()
      elif platform.system() == "Darwin":
         self.__darwinMakeApplication()
         self.__darwinMakeDMG()
      elif platform.system() == "Linux":
         self.__linuxMakeBinaries()
         self.__linuxMakeAppImage()
         self.__linuxMakeDeb()

   def clean( self ):

      utility.printHeading( "Cleaning project..." )

      utility.runCommand(
         'pushd "' + config.synergyCorePath() + '" && '
         'git clean -fdx && '
         "popd" )

      utility.runCommand(
         'pushd "' + config.toplevelPath() + '" && '
         'git clean -fdx && '
         "popd" )